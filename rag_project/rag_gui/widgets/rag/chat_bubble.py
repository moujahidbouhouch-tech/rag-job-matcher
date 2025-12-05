import html
import re
from PyQt5 import QtCore, QtWidgets, QtGui

from rag_project.rag_gui.config.layout import (
    PADDING_MEDIUM,
    BORDER_RADIUS,
    GUI_CHAT_BUBBLE_MAX_WIDTH,
    GUI_CHAT_BUBBLE_MIN_WIDTH,
)


class ChatBubble(QtWidgets.QWidget):
    """A single chat message widget (User or AI) with enhanced markdown rendering."""
    
    # Signal emitted when a citation link like <a href="1">[1]</a> is clicked
    citation_clicked = QtCore.pyqtSignal(str)
    
    def __init__(self, text: str, is_user: bool, parent=None, citations=None):
        super().__init__(parent)
        self.text = text
        self.is_user = is_user
        self.citations = citations or []
        self.citation_map = {str(c.get("label")): c for c in self.citations if c.get("label") is not None}
        self._build_ui()
    
    def _build_ui(self):
        """Build the bubble UI structure."""
        # Main layout for the row (Spacer + Bubble or Bubble + Spacer)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 5)
        
        # The actual colored bubble
        self.bubble_frame = QtWidgets.QFrame()
        self.bubble_frame.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, 
            QtWidgets.QSizePolicy.Minimum
        )
        bubble_layout = QtWidgets.QVBoxLayout(self.bubble_frame)
        bubble_layout.setContentsMargins(12, 8, 12, 8)
        
        # Message Label (Supports Rich Text for links)
        self.lbl = QtWidgets.QLabel()
        self.lbl.setWordWrap(True)
        self.lbl.setTextFormat(QtCore.Qt.RichText)
        self.lbl.setTextInteractionFlags(QtCore.Qt.TextBrowserInteraction)
        self.lbl.setOpenExternalLinks(False)  # We handle links manually
        self.lbl.linkActivated.connect(self.citation_clicked.emit)
        
        # Render content with proper markdown
        rendered_html = self._render_html(self.text, self.is_user)
        
        # Apply the rendered HTML
        self.lbl.setText(f"<div class='bubble-content'>{rendered_html}</div>")
        
        # Font styling
        font = QtGui.QFont()
        font.setPointSize(11)
        self.lbl.setFont(font)
        
        bubble_layout.addWidget(self.lbl)
        
        # Determine Styling based on sender
        if self.is_user:
            layout.addStretch()
            layout.addWidget(self.bubble_frame)
            self.bubble_frame.setObjectName("UserBubble")
            self.lbl.setObjectName("UserBubbleLabel")
        else:
            layout.addWidget(self.bubble_frame)
            self.bubble_frame.setObjectName("AssistantBubble")
            self.lbl.setObjectName("AssistantBubbleLabel")
        
        # Width constraint
        self.bubble_frame.setMaximumWidth(GUI_CHAT_BUBBLE_MAX_WIDTH)
        self.bubble_frame.setMinimumWidth(GUI_CHAT_BUBBLE_MIN_WIDTH)
    
    def _render_html(self, text: str, is_user: bool) -> str:
        """
        Render markdown-ish content to HTML with comprehensive support.
        
        For users: Simple escape + newline preservation
        For AI: Full markdown rendering with fallback
        """
        # Users: plain escape + newline handling
        if is_user:
            return html.escape(text).replace("\n", "<br>")
        
        # Assistants: Try full markdown, fallback to enhanced regex
        try:
            import markdown
            # Use extensions for better rendering
            return markdown.markdown(
                text, 
                extensions=[
                    'nl2br',      # Newline to <br>
                    'tables',     # Table support
                    'fenced_code' # Code blocks
                ]
            )
        except (ImportError, Exception):
            # Fallback: Enhanced regex-based parser
            return self._fallback_markdown_parser(text)
    
    def _fallback_markdown_parser(self, text: str) -> str:
        """
        Enhanced fallback markdown parser using regex.
        Handles: headers, bold, italic, lists, code, emoji, links
        """
        # Escape HTML first to prevent injection
        escaped = html.escape(text)
        
        # ===== PHASE 1: Block-level elements =====
        
        # Headers (must be at start of line, handle emoji)
        # ### Header → <h3>Header</h3>
        escaped = re.sub(
            r'^(#{1,3})\s*(.+?)$',
            lambda m: f"<h{len(m.group(1))}>{m.group(2)}</h{len(m.group(1))}>",
            escaped,
            flags=re.MULTILINE
        )
        
        # Code blocks (```)
        escaped = re.sub(
            r'```(\w*)\n(.*?)```',
            r'<pre><code class="\1">\2</code></pre>',
            escaped,
            flags=re.DOTALL
        )
        
        # ===== PHASE 2: Lists =====
        
        # Bullet lists: Handle nested structure
        # Match: "- item" or "• item" at start of line
        lines = escaped.split('\n')
        in_list = False
        processed_lines = []
        
        for line in lines:
            # Check if line is a list item
            list_match = re.match(r'^[\s]*([-•\*])\s+(.+)$', line)
            
            if list_match:
                if not in_list:
                    processed_lines.append('<ul style="margin: 8px 0; padding-left: 20px;">')
                    in_list = True
                # Extract content and preserve nested structure
                content = list_match.group(2)
                processed_lines.append(f'<li style="margin: 4px 0;">{content}</li>')
            else:
                if in_list:
                    processed_lines.append('</ul>')
                    in_list = False
                processed_lines.append(line)
        
        if in_list:
            processed_lines.append('</ul>')
        
        escaped = '\n'.join(processed_lines)
        
        # ===== PHASE 3: Inline elements =====
        
        # Bold: **text** → <strong>text</strong>
        escaped = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', escaped)
        
        # Italic: *text* → <em>text</em> (avoid matching list markers)
        escaped = re.sub(r'(?<!\*)\*(?!\*)(.+?)\*(?!\*)', r'<em>\1</em>', escaped)
        
        # Inline code: `code` → <code>code</code>
        escaped = re.sub(
            r'`([^`]+)`', 
            r'<code style="background-color: rgba(0,0,0,0.1); padding: 2px 4px; border-radius: 3px; font-family: monospace;">\1</code>', 
            escaped
        )
        
        # Links: [text](url) → <a href="url">text</a>
        escaped = re.sub(
            r'\[([^\]]+)\]\(([^\)]+)\)',
            r'<a href="\2" style="color: #0066cc; text-decoration: none;">\1</a>',
            escaped
        )
        
        # ===== PHASE 4: Special formatting =====
        
        # Horizontal rules: --- or ***
        escaped = re.sub(
            r'^(?:---|\*\*\*)$',
            '<hr style="border: none; border-top: 1px solid rgba(128,128,128,0.3); margin: 12px 0;">',
            escaped,
            flags=re.MULTILINE
        )
        
        # Blockquotes: > text
        escaped = re.sub(
            r'^&gt;\s*(.+)$',
            r'<blockquote style="border-left: 3px solid rgba(128,128,128,0.3); padding-left: 12px; margin: 8px 0; font-style: italic;">\1</blockquote>',
            escaped,
            flags=re.MULTILINE
        )
        
        # ===== PHASE 5: Newlines and paragraphs =====
        
        # Convert remaining newlines to <br>, but not inside block elements
        # Split by block tags first
        parts = re.split(r'(</?(?:h[1-6]|ul|ol|li|pre|code|blockquote)>)', escaped)
        
        processed_parts = []
        in_block = False
        
        for part in parts:
            if re.match(r'<(?:h[1-6]|ul|ol|pre|blockquote)>', part):
                in_block = True
                processed_parts.append(part)
            elif re.match(r'</(?:h[1-6]|ul|ol|pre|blockquote)>', part):
                in_block = False
                processed_parts.append(part)
            elif in_block:
                processed_parts.append(part)
            else:
                # Replace newlines with <br> in text content
                processed_parts.append(part.replace('\n', '<br>'))
        
        return ''.join(processed_parts)

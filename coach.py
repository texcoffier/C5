# pylint: disable=invalid-name,too-many-arguments,too-many-instance-attributes

"""
EFFICIENCY COACH FOR C5

Author: Tomas Delon Gago

This module implements a coaching system to help students
use keyboard shortcuts and efficient editing techniques.

Architecture:
    - Coach class: main manager that coordinates all coaches
    - CoachState class: shared state between all coaches (cursor position, streaks, etc.)
    - Coach subclasses: each coach detects a specific inefficient pattern

Usage:
    coach = create_coach(options_dict)

    # In an event handler:
    # previous_position is optional; pass it if available
    result = coach.analyse(event, text, cursor_position, previous_position)
    if result:
        show_popup(result['message'])
        if 'restore_cursor_position' in result['actions']:
            restore_position(result['actions']['restore_cursor_position'])

Available coach options (configure in options.py):
    - coach_tip_level: Enable/disable coaching system (0=disabled, 1=enabled)
    - coach_cooldown: Minimum delay between tips in milliseconds (default: 5000ms)

    - coach_mouse_short_move: Detect mouse for short movements instead of arrow keys
        • coach_mouse_short_move_chars: Max horizontal distance (default: 5)
        • coach_mouse_short_move_drift: Max column drift for vertical (default: 3)

    - coach_mouse_line_bounds: Detect mouse to go to line beginning/end instead of Home/End

    - coach_many_horizontal_arrows: Detect many horizontal arrows instead of Ctrl+arrows or Home/End
        • coach_many_horizontal_arrows_count: Threshold (default: 15)

    - coach_many_vertical_arrows: Detect many vertical arrows instead of PgUp/PgDn
        • coach_many_vertical_arrows_count: Threshold (default: 10)

    - coach_arrow_then_backspace: Detect → then Backspace instead of Delete key
        • coach_arrow_then_backspace_count: Repetitions before tip (default: 3)

    - coach_retype_after_delete: Detect retyping deleted text instead of Ctrl+Z
        • coach_retype_after_delete_chars: Min identical chars (default: 10)

    - coach_scroll_full_document: Detect scrolling to document boundaries instead of Ctrl+Home/End
        • coach_scroll_full_document_edge_lines: Lines near edge (default: 3)
        • coach_scroll_full_document_min_lines: Min file lines (default: 30)

    - coach_letter_select_word: Detect selecting word letter-by-letter instead of double-click or Ctrl+Shift+arrows
        • coach_letter_select_word_min_chars: Min chars selected (default: 8)

    - coach_delete_word_char_by_char: Detect deleting word char-by-char instead of Ctrl+Backspace/Delete
        • coach_delete_word_char_by_char_count: Threshold (default: 5)

    - coach_copy_then_delete: Detect Ctrl+C then Delete instead of Ctrl+X
"""

# ════════════════════════════════════════════════════════════════════════════
# COACHING TIP MESSAGES (in French for students)
# ════════════════════════════════════════════════════════════════════════════

COACH_MESSAGES = {
    'mouse_short_move': (
        "🐢 Trop lent avec la souris !<br><br>"
        + "Pour de petits déplacements, vos doigts sont plus rapides que votre main :<br>"
        + "Utilisez <kbd>←</kbd> <kbd>→</kbd> ou <kbd>↑</kbd> <kbd>↓</kbd> au lieu de la souris.<br>"
        + "<em>Astuce pro : gardez vos mains sur le clavier ! 🎮</em>"
    ),
    'mouse_line_bounds': (
        "🎯 Vous visez le début ou la fin de ligne ?<br><br>"
        + "Arrêtez de cliquer comme un pigeon ! 🐦<br>"
        + "Utilisez <kbd>↖ Home</kbd> pour le début, "
        + "<kbd>End</kbd> pour la fin.<br>"
        + "Sur portable : <kbd>Fn</kbd> + <kbd>←</kbd> ou <kbd>Fn</kbd> + <kbd>→</kbd>"
    ),
    'many_horizontal_arrows': (
        "⌨️ Wow, vous aimez vraiment cette touche fléchée !<br><br>"
        + "Pour aller plus vite :<br>"
        + "• <kbd>Ctrl</kbd> + <kbd>←</kbd> / <kbd>Ctrl</kbd> + <kbd>→</kbd> = sauter de mot en mot 🦘<br>"
        + "• <kbd>Home</kbd>/<kbd>End</kbd> = début/fin de ligne ⚡<br>"
        + "<em>Vos doigts vous remercieront !</em>"
    ),
    'many_vertical_arrows': (
        "🏃 Marathon de touches fléchées détecté !<br><br>"
        + "Vous descendez l'Everest ligne par ligne ? 🏔️<br>"
        + "• <kbd>PgUp</kbd>/<kbd>PgDn</kbd> = sauter de page en page<br>"
        + "• <kbd>Ctrl</kbd> + <kbd>Home</kbd> / <kbd>Ctrl</kbd> + <kbd>End</kbd> = début/fin du fichier<br>"
        + "<em>C'est comme un ascenseur pour votre code ! 🛗</em>"
    ),
    'arrow_then_backspace': (
        "🤔 Hmm, vous faites compliqué là...<br><br>"
        + "Au lieu de <kbd>→</kbd> puis <kbd>⌫</kbd>, utilisez simplement "
        + "<kbd>⌦</kbd> (Suppr) !<br>"
        + "C'est 2 touches → 1 touche. Même votre calculatrice approuverait. 🧮<br>"
        + "<em>Travaillez plus intelligemment, pas plus dur !</em>"
    ),
    'retype_after_delete': (
        "😱 STOP ! Vous retapez ce que vous venez d'effacer !<br><br>"
        + "C'est comme creuser un trou pour le reboucher... 🕳️⛏️<br>"
        + "Utilisez plutôt :<br>"
        + "• <kbd>Ctrl</kbd> + <kbd>Z</kbd> pour annuler<br>"
        + "• <kbd>Ctrl</kbd> + <kbd>Y</kbd> pour rétablir<br>"
        + "<em>Vos doigts ne sont pas un time machine, mais Ctrl+Z oui ! ⏰✨</em>"
    ),
    'scroll_full_document': (
        "🚀 Vous avez atteint le bout du monde !<br><br>"
        + "Pour aller directement au début ou à la fin du fichier :<br>"
        + "• <kbd>Ctrl</kbd> + <kbd>Home</kbd> = début du fichier ⬆️<br>"
        + "• <kbd>Ctrl</kbd> + <kbd>End</kbd> = fin du fichier ⬇️<br>"
        + "<em>Téléportation instantanée ! ✨</em>"
    ),
    'letter_select_word': (
        "🔤 Sélectionner lettre par lettre ? Vraiment ?<br><br>"
        + "Pour sélectionner un mot entier :<br>"
        + "• <kbd>Double-clic</kbd> sur le mot 🖱️<br>"
        + "• <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + "
        + "<kbd>←</kbd> / <kbd>→</kbd> = mot par mot<br>"
        + "<em>Travaillez plus intelligemment ! 🧠</em>"
    ),
    'delete_word_char_by_char': (
        "⌫ Vous effacez un mot entier caractère par caractère ?<br><br>"
        + "Pour supprimer un mot complet d'un coup :<br>"
        + "• <kbd>Ctrl</kbd> + <kbd>Backspace</kbd> = supprimer mot à gauche ⬅️<br>"
        + "• <kbd>Ctrl</kbd> + <kbd>Delete</kbd> = supprimer mot à droite ➡️<br>"
        + "<em>Un mot = une touche ! 💥</em>"
    ),
    'copy_then_delete': (
        "✂️ Copier puis supprimer ? Il y a plus simple !<br><br>"
        + "Au lieu de <kbd>Ctrl</kbd> + <kbd>C</kbd> puis "
        + "<kbd>Delete</kbd>, utilisez directement :<br>"
        + "• <kbd>Ctrl</kbd> + <kbd>X</kbd> = couper (copie + supprime) ✂️<br>"
        + "<em>Deux touches → une touche ! 🚀</em>"
    )
}

# ════════════════════════════════════════════════════════════════════════════
# AUXILIARY FUNCTIONS
# ════════════════════════════════════════════════════════════════════════════

def millisecs():
    """
    Returns the current time in milliseconds.

    Uses Date.now() in JavaScript (via eval for RapydScript).
    """
    # In JavaScript (RapydScript transpiles this to Date.now())
    return eval('Date.now()')  # pylint: disable=eval-used


def get_line_column(text, position):
    """
    Calculates line and column number from an absolute position in the text.

    Args:
        text: The complete editor text
        position: Absolute position (number of characters from the beginning)

    Returns:
        (line, column): Tuple with line number (1-indexed) and column (0-indexed)

    Example:
        text = "abc\\ndef\\nghi"
        get_line_column(text, 5) → (2, 1)  # 'd' is on line 2, column 1
    """
    # Extract text up to the position
    lines = text[:position].split('\n')
    # Number of lines = number of \\n + 1
    line_number = len(lines)
    # Column = length of the last line
    column = len(lines[-1])
    return line_number, column


def coach_debug(message):
    """
    Comment this function content to disable debug trace
    """
    print("COACH DEBUG " + str(message or 'None'))


def prefix_length(text1, text2):
    if text1 == text2:
        return len(text1)
    i = 0
    for a, b in zip(text1, text2):
        if a != b:
            return i
        i += 1
    return i

# ════════════════════════════════════════════════════════════════════════════
# SHARED COACH STATE
# ════════════════════════════════════════════════════════════════════════════

class CoachState:
    """
    Shared state between all coaches.

    This state persists between events and allows coaches to detect
    patterns across multiple interactions (e.g., consecutive arrow key counter).

    Note: This class was initially Coach.State (nested class),
    but RapydScript doesn't support nested classes yet, so
    it has been extracted as a separate class.
    """
    horizontal_streak = 0             # Number of consecutive ← or → arrows
    vertical_streak = 0               # Number of consecutive ↑ or ↓ arrows
    horizontal_direction = None       # Direction of last horizontal arrow
    vertical_direction = None         # Direction of last vertical arrow

    last_mouseup = 0                  # Timestamp of last mouseup

    # Arrow+Backspace detection
    last_arrow_right_time = 0
    last_was_arrow_right = False

    # Retyping detection (character-by-character comparison)
    previous_text_for_retype = ''     # Complete previous text
    last_deleted_text_exact = ''      # Exact deleted text
    last_deleted_position_exact = -1  # Position of deleted text
    last_deleted_time = 0             # Timestamp of last deletion
    text_after_deletion = ''          # Text after deletion
    retype_match_count = 0            # Counter of identical retyped characters

    # Popup cooldown (dict: option → timestamp)
    # Dict of timestamps of last popups (by coach type)
    last_popup = {}

    # Previous cursor position (for movement calculation)
    previous_position = 0


# ════════════════════════════════════════════════════════════════════════════
# MAIN COACH CLASS
# ════════════════════════════════════════════════════════════════════════════

class Coach:
    """
    Main manager of the efficiency coaching system.

    This class coordinates all specific coaches and manages the shared state.
    It provides common utility methods (option checking, cooldown, etc.)

    Architecture:
        - Receives a list of specific coaches in __init__
        - Maintains shared state (CoachState) accessible by all coaches
        - analyse() method iterates over all coaches until finding a detection
        - Each coach implements check() which returns None or a tip
    """

    def __init__(self, coaches, options):
        """
        Initializes the coach with a list of specific coaches.

        Args:
            coach1-coach6: Coach instances (detectors for inefficient patterns)

        Example:
            coach = Coach([
                Mouse_short_move(),
                Mouse_line_bounds(),
                Many_horizontal_arrows(),
                Many_vertical_arrows(),
                Arrow_then_backspace(),
                Retype_after_delete()
                ], options)
        """
        self.coaches = coaches
        self.state = CoachState()
        self.options = options or {}
        # Get cooldown from options (default: 5000ms = 5 seconds)
        self.popup_cooldown = int(options['coach_cooldown'] or 5000)
        self.coach_tip_level = int(self.options['coach_tip_level'] or 0)

    def show_tip(self, option, message, actions=None):
        """
        Attempts to display a tip if conditions are met.

        Args:
            option: Coach option name (to check activation and cooldown)
            message: HTML message of the tip to display
            actions: Optional dict of actions (e.g., {'restore_cursor_position': 42})

        Returns:
            Dict with {'option', 'message', 'actions'} if tip can be displayed
            None if tip is blocked (option disabled, cooldown, dialog visible)

        Note:
            This method checks:
            1. Option is enabled
            3. Cooldown has elapsed (0 by default = no cooldown)
        """
        # Check cooldown
        now = millisecs()
        if option in self.state.last_popup:
            last = self.state.last_popup[option]
        else:
            last = 0

        if now - last < self.popup_cooldown:
            return None

        # Record timestamp and return tip
        self.state.last_popup[option] = now
        return {'option': option, 'message': message, 'actions': actions or {}}

    def check_event_type(self, event, expected_type):
        """
        Returns True if the event if of the expected type (e.g., 'mouseup', 'keydown')
        """
        if expected_type == '*':
            return True
        if event:
            return event.type == expected_type

    def should_check(self, coach, event):
        """
        Returns True if the coach is enabled and must receive the event.
        """
        if not self.coach_tip_level:
            return False
        if not bool(self.options[coach.option] or 0):
            return False
        if not self.check_event_type(event, coach.expected_event_type):
            return False
        return True

    def get_key_info(self, event):
        """
        Extracts key and modifiers from keyboard event.

        Args:
            event: DOM event (must be keydown/keyup)

        Returns:
            Tuple (key, ctrl, shift) where:
                key: Key name (e.g., 'ArrowRight', 'Backspace') or None
                ctrl: True if Ctrl is pressed, False otherwise
                shift: True if Shift is pressed, False otherwise

        Note:
            In JavaScript, event.key and event.ctrlKey return undefined
            if absent, without raising an exception.
        """
        if not event:
            return None, False, False
        key = event.key
        ctrl = bool(event.ctrlKey)
        shift = bool(event.shiftKey)
        return key, ctrl, shift

    def analyse(self, event, text, cursor_position, previous_position=None):
        """
        Main analysis method - checks all coaches.

        This method iterates over all registered coaches and asks each
        to check if it detects an inefficient pattern. The first coach that detects
        something returns a tip, and the analysis stops.

        Args:
            event: DOM event (mouseup, keydown, etc.) or None
            text: Complete editor text
            cursor_position: Current cursor position (number of characters)
            previous_position: Previous cursor position (number of characters), optional

        Returns:
            Dict with {'option', 'message', 'actions'} if a tip was detected
            None if no coach detected an inefficient pattern

        Note:
            - Coaches are checked in registration order
            - Only the first coach that detects something returns a tip
            - Each coach implements its own check() method
        """
        # Optionally update shared previous cursor position
        if previous_position is not None:
            self.state.previous_position = previous_position

        for coach in self.coaches:
            if self.should_check(coach, event):
                result = coach.check(self, event, text, cursor_position)
                if result:
                    return result
        return None


# ════════════════════════════════════════════════════════════════════════════
# SPECIFIC COACHES - INEFFICIENT PATTERN DETECTION
# ════════════════════════════════════════════════════════════════════════════

class Mouse_short_move(Coach):
    """
    Detects small mouse movements (a few characters or lines).

    Detected pattern:
        - Mouse click to move 1-5 characters horizontally (same line)
        - Mouse click to move 1 line vertically while staying in same column

    Suggestion:
        Use arrow keys ← → ↑ ↓ for small movements

    Thresholds (configurable via options):
        - small_char_threshold: Max horizontal distance (option: coach_mouse_short_move_chars, default: 5)
        - max_column_drift: Max column drift for vertical (option: coach_mouse_short_move_drift, default: 3)
        - min_click_delay: 300ms = Minimum delay between clicks to filter double/triple clicks (hardcoded)
    """
    option = 'coach_mouse_short_move'
    message = COACH_MESSAGES['mouse_short_move']
    min_click_delay = 300
    expected_event_type = 'mouseup'

    def check(self, manager, event, text, cursor_position):
        small_char_threshold = 5
        max_column_drift = 3
        if 'coach_mouse_short_move_chars' in manager.options:
            small_char_threshold = manager.options['coach_mouse_short_move_chars']
        if 'coach_mouse_short_move_drift' in manager.options:
            max_column_drift = manager.options['coach_mouse_short_move_drift']

        now = millisecs()
        idle = now - manager.state.last_mouseup
        manager.state.last_mouseup = now
        if idle < self.min_click_delay:
            return None

        previous_position = manager.state.previous_position or 0
        prev_line, prev_col = get_line_column(text, previous_position)
        new_line, new_col = get_line_column(text, cursor_position)
        dy = abs(new_line - prev_line)
        dx = abs(new_col - prev_col)

        if dy == 0 and dx == 0:
            return None

        if dy == 0 and 0 < dx <= small_char_threshold:
            return manager.show_tip(self.option, self.message,
                                   {'restore_cursor_position': previous_position})

        if dy == 1 and dx <= max_column_drift:
            return manager.show_tip(self.option, self.message,
                                   {'restore_cursor_position': previous_position})

        return None


class Mouse_line_bounds(Coach):
    """
    Detects when mouse is used to go to beginning/end of a line.

    Detected pattern:
        - Click on column 0 (line beginning)
        - Click on last column (line end)
        - Without changing lines

    Suggestion:
        Use Home (beginning) or End (end) of line
        On laptop: Fn + ← or Fn + →

    Thresholds (hardcoded):
        - min_movement: 2 characters
        - min_click_delay: 300ms to filter double/triple clicks
    """
    option = 'coach_mouse_line_bounds'
    message = COACH_MESSAGES['mouse_line_bounds']
    min_click_delay = 300
    expected_event_type = 'mouseup'

    def check(self, manager, event, text, cursor_position):
        # Use our own timestamp instead of shared manager.state.last_mouseup
        # because Mouse_short_move updates it before we check
        now = millisecs()
        last_check = getattr(manager.state, 'line_bounds_last_check', 0)
        idle = now - last_check
        manager.state.line_bounds_last_check = now

        if idle < self.min_click_delay:
            return None

        previous_position = manager.state.previous_position or 0
        prev_line, prev_col = get_line_column(text, previous_position)
        new_line, new_col = get_line_column(text, cursor_position)

        if prev_line != new_line:
            return None

        if abs(new_col - prev_col) < 2:
            return None

        lines = text.split('\n')
        if new_line >= 1 and new_line <= len(lines):
            line_length = len(lines[new_line - 1])
            if new_col == 0 or new_col == line_length:
                return manager.show_tip(self.option, self.message)

        return None


class Many_horizontal_arrows(Coach):
    """
    Detects many consecutive horizontal arrows (← →).

    Detected pattern:
        - 15+ consecutive ← or → arrows
        - Without Ctrl (Ctrl+arrow is already efficient)

    Suggestion:
        Use Ctrl + ← / Ctrl + → to jump word by word
        Or Home/End to go to line extremities

    Threshold (configurable via options):
        - threshold: Number of consecutive arrows (option: coach_many_horizontal_arrows_count, default: 15)
    """
    option = 'coach_many_horizontal_arrows'
    message = COACH_MESSAGES['many_horizontal_arrows']
    expected_event_type = 'keydown'

    def check(self, manager, event, text, cursor_position):
        key, ctrl, shift = manager.get_key_info(event)
        if not key:
            return None

        threshold = 15
        if 'coach_many_horizontal_arrows_count' in manager.options:
            threshold = int(manager.options['coach_many_horizontal_arrows_count'])

        state = manager.state

        if key in ('ArrowLeft', 'ArrowRight'):
            if ctrl or shift:
                state.horizontal_streak = 0
                state.horizontal_direction = None
            else:
                direction = key
                last_dir = state.horizontal_direction

                if last_dir and direction != last_dir:
                    state.horizontal_streak = 0

                state.horizontal_direction = direction
                state.horizontal_streak = (state.horizontal_streak or 0) + 1

                if state.horizontal_streak >= threshold:
                    result = manager.show_tip(self.option, self.message)
                    if result:
                        state.horizontal_streak = 0
                        return result
        else:
            state.horizontal_streak = 0
            state.horizontal_direction = None

        return None


class Many_vertical_arrows(Coach):
    """
    Detects many consecutive vertical arrows (↑ ↓).

    Detected pattern:
        - 10+ consecutive ↑ or ↓ arrows
        - Without Ctrl

    Suggestion:
        Use PgUp/PgDn to jump page by page
        Or Ctrl + Home / Ctrl + End to go to beginning/end of file

    Threshold (configurable via options):
        - threshold: Number of consecutive arrows (option: coach_many_vertical_arrows_count, default: 10)
    """
    option = 'coach_many_vertical_arrows'
    message = COACH_MESSAGES['many_vertical_arrows']
    expected_event_type = 'keydown'

    def check(self, manager, event, text, cursor_position):
        """
        Checks if too many consecutive vertical arrows were pressed.
        """
        key, ctrl, shift = manager.get_key_info(event)
        if not key:
            return None

        threshold = 10
        if 'coach_many_vertical_arrows_count' in manager.options:
            threshold = int(manager.options['coach_many_vertical_arrows_count'])

        state = manager.state

        if key in ('ArrowUp', 'ArrowDown'):
            if ctrl or shift:
                state.vertical_streak = 0
                state.vertical_direction = None
            else:
                direction_v = key
                last_dir_v = state.vertical_direction

                if last_dir_v and direction_v != last_dir_v:
                    state.vertical_streak = 0

                state.vertical_direction = direction_v
                state.vertical_streak = (state.vertical_streak or 0) + 1

                if state.vertical_streak >= threshold:
                    result = manager.show_tip(self.option, self.message)
                    if result:
                        state.vertical_streak = 0
                        return result
        else:
            state.vertical_streak = 0
            state.vertical_direction = None

        return None


class Arrow_then_backspace(Coach):
    """
    Detects repeated sequences → then Backspace (instead of using Delete).

    Detected pattern:
        - Arrow → that moves cursor one character
        - Followed by Backspace within 2 seconds
        - Without Ctrl
        - Repeated multiple times (threshold configurable)

    Suggestion:
        Use Delete key to delete the character to the right

    Thresholds:
        - max_delay: 2000ms between arrow and backspace (hardcoded)
        - min_count: Minimum repetitions before showing tip (option: coach_arrow_then_backspace_count, default: 3)
    """
    option = 'coach_arrow_then_backspace'
    message = COACH_MESSAGES['arrow_then_backspace']
    expected_event_type = 'keydown'

    def check(self, manager, event, text, cursor_position):
        min_count = 3
        if 'coach_arrow_then_backspace_count' in manager.options:
            min_count = int(manager.options['coach_arrow_then_backspace_count'])

        key, ctrl, _ = manager.get_key_info(event)
        if not key:
            return None

        state = manager.state
        now = millisecs()

        if key == 'ArrowRight' and not ctrl:
            state.last_arrow_right_time = now
            state.last_was_arrow_right = True

        elif key == 'Backspace' and not ctrl:
            last_was_arrow = getattr(state, 'last_was_arrow_right', False)
            last_arrow_time = getattr(state, 'last_arrow_right_time', 0)
            delta = now - last_arrow_time

            if last_was_arrow and delta < 2000:
                streak = getattr(state, 'arrow_backspace_streak', 0) + 1
                state.arrow_backspace_streak = streak

                if streak >= min_count:
                    result = manager.show_tip(self.option, self.message)
                    if result:
                        state.arrow_backspace_streak = 0
                        state.last_was_arrow_right = False
                        return result

                state.last_was_arrow_right = False
            else:
                state.arrow_backspace_streak = 0
                state.last_was_arrow_right = False

        else:
            state.arrow_backspace_streak = 0
            state.last_was_arrow_right = False

        return None


class Retype_after_delete(Coach):
    """
    Detects when deleted text is retyped identically.

    Detected pattern:
        - Deletion of text
        - Retyping the same text character by character

    Suggestion:
        Use Ctrl + Z (undo) and Ctrl + Y (redo) instead of retyping

    Strategy:
        - Detects deletions and keeps the exact deleted text
        - Compares retyped text character by character with deleted text
        - Alerts when 8+ identical characters have been retyped

    Thresholds (configurable via options):
        - min_chars_threshold: Minimum identical chars retyped (option: coach_retype_after_delete_chars, default: 8)
        - max_delay_ms: Maximum time between deletion and retyping (hardcoded: 10000ms = 10 seconds)
    """
    option = 'coach_retype_after_delete'
    message = COACH_MESSAGES['retype_after_delete']
    max_delay_ms = 10000
    expected_event_type = '*'

    def check(self, manager, event, text, cursor_position):
        """
        Checks if deleted text is being retyped IDENTICALLY.

        Strategy:
        1. Detect deletion: save the EXACT deleted text
        2. Detect typing: compare character by character with deleted text
        3. Count how many IDENTICAL characters have been retyped
        4. Show tip only if threshold+ identical characters are retyped

        Thresholds (configurable via options):
            - min_chars_threshold: Minimum identical chars retyped (option: coach_retype_after_delete_chars, default: 10)
            - max_delay_ms: Maximum time between deletion and retyping (hardcoded: 10000ms = 10 seconds)
        """
        min_chars_threshold = 10
        if 'coach_retype_after_delete_chars' in manager.options:
            min_chars_threshold = int(manager.options['coach_retype_after_delete_chars'])

        state = manager.state
        now = millisecs()
        previous_text = getattr(state, 'previous_text_for_retype', '')

        if len(text) < len(previous_text):
            deleted_length = len(previous_text) - len(text)

            deleted_position = prefix_length(text, previous_text)
            deleted_text = previous_text[deleted_position:deleted_position + deleted_length]

            last_deletion_time = getattr(state, 'last_deleted_time', 0)
            accumulated_deleted = getattr(state, 'last_deleted_text_exact', '')

            if (now - last_deletion_time) < 2000 and len(accumulated_deleted) > 0:
                if deleted_position == len(text):
                    accumulated_deleted = accumulated_deleted + deleted_text
                else:
                    accumulated_deleted = deleted_text + accumulated_deleted
            else:
                accumulated_deleted = deleted_text

            state.text_after_deletion = text

            state.last_deleted_text_exact = accumulated_deleted
            state.last_deleted_position_exact = deleted_position
            state.last_deleted_time = now
            state.retype_match_count = 0

        elif len(text) > len(previous_text):
            last_deleted_time = getattr(state, 'last_deleted_time', 0)
            last_deleted_text = getattr(state, 'last_deleted_text_exact', '')

            if (now - last_deleted_time) < self.max_delay_ms and len(last_deleted_text) >= 3:
                text_after_deletion = getattr(state, 'text_after_deletion', '')

                total_added_text = ''
                added_in_this_event = 0
                if len(text) > len(text_after_deletion):
                    added_length = len(text) - len(text_after_deletion)
                    added_position = prefix_length(text_after_deletion, text)
                    total_added_text = text[added_position:added_position + added_length]

                added_in_this_event = len(text) - len(previous_text)

                match_count = prefix_length(total_added_text, last_deleted_text)

                if added_in_this_event >= 5:
                    state.last_deleted_time = 0
                    state.retype_match_count = 0
                    state.last_deleted_text_exact = ''
                else:
                    state.retype_match_count = match_count

                    if match_count >= min_chars_threshold:
                        result = manager.show_tip(self.option, self.message)
                        if result:
                            state.last_deleted_time = 0
                            state.retype_match_count = 0
                            state.last_deleted_text_exact = ''
                            state.previous_text_for_retype = text
                            return result

        state.previous_text_for_retype = text

        return None


class Scroll_full_document(Coach):
    """
    Detects when user scrolls from top to bottom (or vice versa) of document.

    Detected pattern:
        - User was in the first N lines
        - Then moved to the last N lines (or vice versa)
        - File has at least M lines
        - Movement happened via scroll/PgUp/PgDn/click (not Ctrl+Home/End)

    Suggestion:
        Use Ctrl + Home to go to beginning
        Use Ctrl + End to go to end of file

    Thresholds (configurable via options):
        - edge_lines: Lines from edge to consider top/bottom (option: coach_scroll_full_document_edge_lines, default: 3)
        - min_lines: Minimum file lines to activate (option: coach_scroll_full_document_min_lines, default: 30)
    """
    option = 'coach_scroll_full_document'
    message = COACH_MESSAGES['scroll_full_document']
    expected_event_type = '*'

    def check(self, manager, _event, text, cursor_position):
        # Get thresholds from options (with defaults)
        edge_lines = 3
        min_lines = 30
        if 'coach_scroll_full_document_edge_lines' in manager.options:
            edge_lines = int(manager.options['coach_scroll_full_document_edge_lines'])
        if 'coach_scroll_full_document_min_lines' in manager.options:
            min_lines = int(manager.options['coach_scroll_full_document_min_lines'])

        current_line, _ = get_line_column(text, cursor_position)
        total_lines = len(text.split('\n'))

        if total_lines < min_lines:
            return None

        state = manager.state

        at_top = current_line <= edge_lines
        at_bottom = current_line > total_lines - edge_lines

        previous_zone = getattr(state, 'scroll_previous_zone', None)

        if at_top:
            current_zone = 'top'
        elif at_bottom:
            current_zone = 'bottom'
        else:
            current_zone = 'middle'

        if previous_zone and current_zone != previous_zone:
            if (previous_zone == 'top' and current_zone == 'bottom') or \
               (previous_zone == 'bottom' and current_zone == 'top'):
                # User scrolled across the full document
                result = manager.show_tip(self.option, self.message)
                if result:
                    state.scroll_previous_zone = current_zone
                    return result

        state.scroll_previous_zone = current_zone

        return None


class Letter_select_word(Coach):
    """
    Détecte la sélection lettre par lettre d'un mot entier et suggère des méthodes plus efficaces.

    Detected pattern:
        - 4+ consecutive Shift + ← or Shift + → (selecting character by character)

    Suggestion:
        Use double-click or Ctrl+Shift+arrows to select word by word

    Threshold (configurable via options):
        - threshold: Number of consecutive Shift+arrows (option: coach_letter_select_word_min_chars, default: 8)
    """
    option = 'coach_letter_select_word'
    message = COACH_MESSAGES['letter_select_word']
    expected_event_type = 'keydown'

    def check(self, manager, event, _text, _cursor_position):
        key, ctrl, shift = manager.get_key_info(event)
        if not key:
            return None

        threshold = 8
        if 'coach_letter_select_word_min_chars' in manager.options:
            threshold = int(manager.options['coach_letter_select_word_min_chars'])

        state = manager.state

        if key in ('ArrowLeft', 'ArrowRight'):
            if shift and not ctrl:
                state.letter_select_streak = getattr(state, 'letter_select_streak', 0) + 1

                if state.letter_select_streak >= threshold:
                    result = manager.show_tip(self.option, self.message)
                    if result:
                        state.letter_select_streak = 0
                        return result
            else:
                state.letter_select_streak = 0
        else:
            state.letter_select_streak = 0

        return None


class Delete_word_char_by_char(Coach):
    """
    Detects deletion of a word character by character using Backspace or Delete.

    Detected pattern:
        - 5+ consecutive Backspace or Delete presses
        - Without Ctrl (Ctrl+Backspace/Delete is already efficient)

    Suggestion:
        Use Ctrl + Backspace to delete word to the left
        Use Ctrl + Delete to delete word to the right

    Threshold (configurable via options):
        - threshold: Number of consecutive delete keys (option: coach_delete_word_char_by_char_count, default: 5)
    """
    option = 'coach_delete_word_char_by_char'
    message = COACH_MESSAGES['delete_word_char_by_char']
    expected_event_type = 'keydown'

    def check(self, manager, event, _text, _cursor_position):
        key, ctrl, _ = manager.get_key_info(event)
        if not key:
            return None

        threshold = 5
        if 'coach_delete_word_char_by_char_count' in manager.options:
            threshold = int(manager.options['coach_delete_word_char_by_char_count'])

        state = manager.state

        if key in ('Backspace', 'Delete'):
            if ctrl:
                state.delete_char_streak = 0
            else:
                state.delete_char_streak = getattr(state, 'delete_char_streak', 0) + 1

                if state.delete_char_streak >= threshold:
                    result = manager.show_tip(self.option, self.message)
                    if result:
                        state.delete_char_streak = 0
                        return result
        else:
            state.delete_char_streak = 0

        return None


class Copy_then_delete(Coach):
    """
    Detects when user copies text and then deletes it (instead of using Ctrl+X to cut).

    Detected pattern:
        - Ctrl+C followed by Delete/Backspace within 3 seconds

    Suggestion:
        Use Ctrl+X to cut (copy + delete in one operation)

    Threshold:
        - max_delay: 3000ms between copy and delete
    """
    option = 'coach_copy_then_delete'
    message = COACH_MESSAGES['copy_then_delete']
    max_delay = 3000  # milliseconds
    expected_event_type = 'keydown'

    def check(self, manager, event, _text, _cursor_position):
        """
        Checks if user copied then deleted (instead of cutting).

        Strategy:
        1. Detect Ctrl+C: mark timestamp
        2. Detect Delete/Backspace after Ctrl+C: show tip

        Assumes Ctrl+C is only used when there's a selection.
        """
        key, ctrl, _ = manager.get_key_info(event)
        if not key:
            return None

        state = manager.state
        now = millisecs()

        if key == 'c' and ctrl:
            state.copy_timestamp = now
            return None

        if key in ('Delete', 'Backspace') and not ctrl:
            copy_time = getattr(state, 'copy_timestamp', 0)
            if copy_time > 0 and (now - copy_time) < self.max_delay:
                state.copy_timestamp = 0
                return manager.show_tip(self.option, self.message)

        if key not in ('c', 'Delete', 'Backspace'):
            state.copy_timestamp = 0

        return None


def create_coach(options):
    coach = Coach(
        [
        Mouse_short_move(),
        Mouse_line_bounds(),
        Many_horizontal_arrows(),
        Many_vertical_arrows(),
        Arrow_then_backspace(),
        Retype_after_delete(),
        Scroll_full_document(),
        Letter_select_word(),
        Delete_word_char_by_char(),
        Copy_then_delete()
        ],
        options
    )
    if coach.coach_tip_level:
        return coach
    # Coach not activated.


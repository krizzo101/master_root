# Terminal Visualization Guidelines

## Overview
This document provides comprehensive guidelines for terminal visualization in monitoring tools, focusing on color systems, accessibility, and best practices for log visualization.

## ANSI Color Codes & Terminal Compatibility

### Basic ANSI Escape Sequences
```
Format: \033[<code>m or \x1b[<code>m
Reset: \033[0m
```

### Standard Color Codes
```
# Foreground Colors (30-37, 90-97)
Black:   30 (dark: 90)
Red:     31 (bright: 91)
Green:   32 (bright: 92)
Yellow:  33 (bright: 93)
Blue:    34 (bright: 94)
Magenta: 35 (bright: 95)
Cyan:    36 (bright: 96)
White:   37 (bright: 97)

# Background Colors (40-47, 100-107)
Add 10 to foreground codes for background colors

# Styles
Bold:      1
Dim:       2
Italic:    3
Underline: 4
Blink:     5
Reverse:   7
```

### 256-Color Support
```
Foreground: \033[38;5;<color>m (0-255)
Background: \033[48;5;<color>m (0-255)
```

### True Color (24-bit RGB)
```
Foreground: \033[38;2;<r>;<g>;<b>m
Background: \033[48;2;<r>;<g>;<b>m
```

### Terminal Compatibility
- **Full Support**: Linux terminals, macOS Terminal/iTerm2, Windows Terminal
- **Partial Support**: Windows CMD (requires ANSI mode enabled)
- **Detection**: Check TERM environment variable, TTY status
- **Fallback**: Always provide --no-color option

## Log Level Color Coding Standards

### Industry Standard Color Scheme
```
TRACE:   Gray/Dim     (\033[90m)
DEBUG:   Cyan         (\033[36m)
INFO:    Green        (\033[32m)
WARN:    Yellow       (\033[93m)
ERROR:   Red          (\033[91m)
FATAL:   Red+Bold     (\033[1;91m)
```

### Alternative High-Contrast Scheme
```
TRACE:   White+Dim    (\033[2;37m)
DEBUG:   Blue         (\033[94m)
INFO:    Default      (no color)
WARN:    Yellow+Bold  (\033[1;93m)
ERROR:   Red+Bold     (\033[1;91m)
FATAL:   Red+Reverse  (\033[7;91m)
```

## Accessibility Considerations

### Color Blind Friendly Palettes

#### Deuteranopia/Protanopia Safe (No Red-Green)
```
Primary Palette:
- Blue:    #0173B2 (Info/Normal)
- Orange:  #DE8F05 (Warning)
- Purple:  #CC78BC (Error)
- Gray:    #949494 (Debug)
- Yellow:  #ECE133 (Highlight)
- Cyan:    #56B4E9 (Success)
```

#### Universal Design Palette
```
Safe Combinations:
- Blue + Orange (high contrast)
- Purple + Yellow (distinguishable)
- Black + White (maximum contrast)
- Use patterns/symbols alongside colors
```

### Accessibility Best Practices
1. **Never rely solely on color** - Use symbols, text prefixes, indentation
2. **Provide color scheme options** - Normal, High Contrast, Colorblind Safe
3. **Support NO_COLOR environment variable**
4. **Use semantic HTML in web terminals**
5. **Test with colorblind simulators**
6. **Minimum contrast ratio**: 4.5:1 for normal text, 3:1 for large text

## Emoji Usage in Terminals

### Universal Support Emojis
```
Status Indicators:
✓ ✗ ⚠ ℹ ⚡ ⚙ 🔧 📊 🔍 📝

Log Levels:
🔍 DEBUG
ℹ️  INFO
⚠️  WARNING
❌ ERROR
💀 FATAL

Process States:
▶️  Running
⏸️  Paused
⏹️  Stopped
🔄 Restarting
✅ Success
❌ Failed
```

### Terminal Compatibility
- **Full Support**: macOS, modern Linux, Windows Terminal
- **Partial Support**: Git Bash, older terminals
- **Fallback Strategy**: Detect terminal capabilities, provide ASCII alternatives

### Emoji Best Practices
1. **Use sparingly** - Don't overwhelm the interface
2. **Consistent meaning** - Same emoji = same concept
3. **Provide alternatives** - --no-emoji flag
4. **Test rendering** - Some emojis display differently
5. **Avoid complex emojis** - Stick to simple, widely supported ones

## Visual Indicators for Different Log Types

### Hierarchical Indentation
```
[SYSTEM] Starting application
  ├─ [MODULE] Loading configuration
  │   ├─ [CONFIG] Reading file: config.yml
  │   └─ [CONFIG] Validation passed
  └─ [MODULE] Initializing database
      └─ [DB] Connected to PostgreSQL
```

### Severity Indicators
```
[TRACE] ... (gray, minimal)
[DEBUG] ... (cyan, verbose)
[INFO]  ... (green, standard)
[WARN]  ⚠️  ... (yellow, highlighted)
[ERROR] ❌ ... (red, prominent)
[FATAL] 💀 ... (red+bold+blink)
```

### Timestamp Formats
```
Compact:  [14:23:45]
ISO:      [2024-01-15T14:23:45Z]
Relative: [+0.234s]
Delta:    [Δ 1.2s]
```

## Monitoring Tool Examples

### Kubernetes/Docker Tools
```
# kubectl/stern style
[pod-name-abc123] [container] 2024-01-15 14:23:45 INFO Starting service
[pod-name-def456] [sidecar]   2024-01-15 14:23:46 WARN Connection timeout

# Color by pod/container
# Use --color=auto|always|never
```

### Prometheus/Grafana Style
```
# Semantic coloring
Green:  Healthy/Success metrics
Yellow: Warning thresholds
Red:    Critical/Error states
Blue:   Informational
Gray:   No data/Unknown
```

## Implementation Recommendations

### Color Management Class
```python
class ColorScheme:
    SCHEMES = {
        'default': {...},
        'high_contrast': {...},
        'colorblind_safe': {...},
        'monochrome': {...}
    }
    
    def __init__(self, scheme='default', force_color=None):
        self.enabled = self._detect_color_support(force_color)
        self.scheme = self.SCHEMES[scheme]
```

### Progressive Enhancement
1. Start with plain text
2. Add basic 8-color support
3. Enhance with 256-color palette
4. Optional true color for capable terminals
5. Always respect NO_COLOR and --no-color

### Performance Considerations
- Cache color codes to avoid repeated string formatting
- Batch color operations for better performance
- Use compiled regex for color stripping
- Minimize ANSI escape sequences in piped output

## Testing Guidelines

### Terminal Testing Matrix
- Linux: gnome-terminal, konsole, xterm
- macOS: Terminal.app, iTerm2
- Windows: cmd, PowerShell, Windows Terminal
- Cross-platform: VS Code terminal, tmux, screen

### Automated Testing
```bash
# Test color output
TERM=xterm-256color ./app
TERM=dumb ./app  # Should disable colors
NO_COLOR=1 ./app  # Should disable colors

# Test accessibility
# Use colorblind simulation tools
# Verify with screen readers
```

## References & Tools

### Color Tools
- **ColorBrewer**: Colorblind-safe palettes
- **Contrast Checkers**: WCAG compliance verification
- **Terminal Color Test**: `curl -s https://raw.githubusercontent.com/JohnMorales/dotfiles/master/colors/24-bit-color.sh | bash`

### Libraries
- **Python**: colorama, termcolor, rich
- **JavaScript**: chalk, colors, ansi-colors
- **Go**: fatih/color, gookit/color
- **Rust**: termcolor, colored

### Standards
- ANSI X3.64 / ECMA-48
- ISO 8613-6 (24-bit color)
- WCAG 2.1 (Web Content Accessibility Guidelines)
- NO_COLOR standard (https://no-color.org)

## Quick Reference Card

```
# Enable colors (bash/zsh)
export TERM=xterm-256color
export COLORTERM=truecolor

# Disable colors
export NO_COLOR=1

# Test terminal capabilities
tput colors  # Number of colors supported
echo $TERM   # Terminal type

# Common patterns
SUCCESS="\\033[92m✓\\033[0m"
ERROR="\\033[91m✗\\033[0m"
WARNING="\\033[93m⚠\\033[0m"
INFO="\\033[94mℹ\\033[0m"
```
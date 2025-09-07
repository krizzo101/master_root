# Visual Design System for Agent Orchestrator

## Overview
This document defines the comprehensive visual design system for the agent orchestrator, including color coding, role indicators, swarm visualization, and terminal compatibility guidelines.

## Color Palette Specification

### Primary Agent Colors (256-color compatible)
```python
# Agent color assignment pool (ANSI 256-color codes)
AGENT_COLORS = {
    'primary': [
        {'code': 39,  'rgb': '#00afff', 'name': 'Deep Sky Blue'},
        {'code': 202, 'rgb': '#ff5f00', 'name': 'Orange'},
        {'code': 118, 'rgb': '#87ff00', 'name': 'Chartreuse'},
        {'code': 199, 'rgb': '#ff00af', 'name': 'Deep Pink'},
        {'code': 226, 'rgb': '#ffff00', 'name': 'Yellow'},
        {'code': 51,  'rgb': '#00ffff', 'name': 'Cyan'},
        {'code': 93,  'rgb': '#8700ff', 'name': 'Violet'},
        {'code': 208, 'rgb': '#ff8700', 'name': 'Dark Orange'},
    ],
    'secondary': [
        {'code': 147, 'rgb': '#afafff', 'name': 'Light Slate Blue'},
        {'code': 114, 'rgb': '#87ff87', 'name': 'Light Green'},
        {'code': 218, 'rgb': '#ffafff', 'name': 'Pink'},
        {'code': 180, 'rgb': '#d7af87', 'name': 'Tan'},
    ]
}
```

### Accessibility-First Color Schemes

#### Colorblind Safe Palette (Deuteranopia/Protanopia)
```python
COLORBLIND_SAFE = {
    'primary_blue':   {'ansi': 33,  'hex': '#0173B2', 'use': 'Normal/Info'},
    'orange':         {'ansi': 208, 'hex': '#DE8F05', 'use': 'Warning/Important'},
    'purple':         {'ansi': 135, 'hex': '#CC78BC', 'use': 'Error/Critical'},
    'gray':           {'ansi': 244, 'hex': '#949494', 'use': 'Debug/Trace'},
    'yellow':         {'ansi': 226, 'hex': '#ECE133', 'use': 'Highlight'},
    'cyan':           {'ansi': 51,  'hex': '#56B4E9', 'use': 'Success'},
    'reddish_purple': {'ansi': 197, 'hex': '#E56B5D', 'use': 'Fatal/Severe'},
}
```

#### High Contrast Mode
```python
HIGH_CONTRAST = {
    'background': 'black',    # Terminal default
    'foreground': 'white',    # Maximum contrast
    'accent_1':   'yellow',   # ANSI 93 (bright yellow)
    'accent_2':   'cyan',     # ANSI 96 (bright cyan)
    'warning':    'orange',   # ANSI 208
    'error':      'red',      # ANSI 91 (bright red)
    'success':    'green',    # ANSI 92 (bright green)
}
```

## Agent Color Assignment Algorithm

### Dynamic Color Assignment
```python
class AgentColorAssigner:
    """Assigns unique, distinguishable colors to agents"""

    def __init__(self, scheme='default'):
        self.assigned_colors = {}
        self.color_pool = self._get_color_pool(scheme)
        self.next_index = 0

    def assign_color(self, agent_id: str) -> dict:
        """Assign a unique color to an agent"""
        if agent_id in self.assigned_colors:
            return self.assigned_colors[agent_id]

        # Use hash-based assignment for consistency
        hash_val = hash(agent_id)

        # Primary assignment strategy
        if len(self.assigned_colors) < len(self.color_pool['primary']):
            color_idx = hash_val % len(self.color_pool['primary'])
            # Ensure uniqueness
            while color_idx in [c['index'] for c in self.assigned_colors.values()]:
                color_idx = (color_idx + 1) % len(self.color_pool['primary'])
            color = self.color_pool['primary'][color_idx]
            color['index'] = color_idx
        else:
            # Secondary assignment with pattern modifiers
            base_idx = hash_val % len(self.color_pool['primary'])
            color = self.color_pool['primary'][base_idx].copy()
            color['modifier'] = self._get_pattern_modifier(len(self.assigned_colors))

        self.assigned_colors[agent_id] = color
        return color

    def _get_pattern_modifier(self, count: int) -> str:
        """Get visual pattern modifier for color reuse"""
        patterns = ['bold', 'underline', 'italic', 'dim']
        return patterns[count % len(patterns)]
```

### Color Distance Algorithm
```python
def color_distance(color1: tuple, color2: tuple) -> float:
    """Calculate perceptual distance between colors (CIE Delta E)"""
    # Simplified weighted Euclidean distance in RGB
    r_mean = (color1[0] + color2[0]) / 2
    delta_r = color1[0] - color2[0]
    delta_g = color1[1] - color2[1]
    delta_b = color1[2] - color2[2]

    weight_r = 2 + r_mean/256
    weight_g = 4
    weight_b = 2 + (255-r_mean)/256

    return math.sqrt(
        weight_r * delta_r**2 +
        weight_g * delta_g**2 +
        weight_b * delta_b**2
    )
```

## Role Indicator Mapping

### Agent Role Indicators
```python
ROLE_INDICATORS = {
    # Primary Roles
    'orchestrator':     {'symbol': '🎭', 'ascii': '[O]', 'color': 'cyan',    'style': 'bold'},
    'coordinator':      {'symbol': '🎯', 'ascii': '[C]', 'color': 'blue',    'style': 'bold'},
    'worker':          {'symbol': '⚙️', 'ascii': '[W]', 'color': 'default', 'style': 'normal'},
    'specialist':      {'symbol': '🔧', 'ascii': '[S]', 'color': 'yellow',  'style': 'normal'},

    # Functional Roles
    'analyzer':        {'symbol': '🔍', 'ascii': '[A]', 'color': 'green',   'style': 'normal'},
    'validator':       {'symbol': '✓',  'ascii': '[V]', 'color': 'green',   'style': 'normal'},
    'reporter':        {'symbol': '📊', 'ascii': '[R]', 'color': 'blue',    'style': 'normal'},
    'monitor':         {'symbol': '👁️', 'ascii': '[M]', 'color': 'purple',  'style': 'normal'},

    # State Roles
    'leader':          {'symbol': '👑', 'ascii': '[L]', 'color': 'gold',    'style': 'bold'},
    'follower':        {'symbol': '🐝', 'ascii': '[F]', 'color': 'default', 'style': 'dim'},
    'independent':     {'symbol': '🦅', 'ascii': '[I]', 'color': 'orange',  'style': 'normal'},

    # Error States
    'failed':          {'symbol': '❌', 'ascii': '[X]', 'color': 'red',     'style': 'bold'},
    'timeout':         {'symbol': '⏱️', 'ascii': '[T]', 'color': 'yellow',  'style': 'blink'},
    'blocked':         {'symbol': '🚫', 'ascii': '[B]', 'color': 'red',     'style': 'reverse'},
}
```

### Status Indicators
```python
STATUS_INDICATORS = {
    'idle':        {'symbol': '⏸',  'ascii': '[-]', 'color': 'gray'},
    'starting':    {'symbol': '🚀', 'ascii': '[>]', 'color': 'yellow'},
    'running':     {'symbol': '▶',  'ascii': '[*]', 'color': 'green'},
    'processing':  {'symbol': '⚡', 'ascii': '[~]', 'color': 'cyan'},
    'completed':   {'symbol': '✅', 'ascii': '[✓]', 'color': 'green'},
    'error':       {'symbol': '❌', 'ascii': '[!]', 'color': 'red'},
    'warning':     {'symbol': '⚠',  'ascii': '[?]', 'color': 'yellow'},
    'paused':      {'symbol': '⏸',  'ascii': '[|]', 'color': 'blue'},
    'terminated':  {'symbol': '⏹',  'ascii': '[.]', 'color': 'red'},
}
```

## Swarm Visualization System

### Swarm Pattern Indicators
```python
SWARM_PATTERNS = {
    'forming': {
        'symbol': '🌀',
        'ascii': '(◐◓◑◒)',  # Rotating animation
        'color': 'yellow',
        'description': 'Agents organizing into swarm'
    },
    'aligned': {
        'symbol': '▣',
        'ascii': '[===]',
        'color': 'green',
        'description': 'Swarm operating in harmony'
    },
    'diverging': {
        'symbol': '⟨⟩',
        'ascii': '<|>',
        'color': 'orange',
        'description': 'Swarm splitting into sub-groups'
    },
    'converging': {
        'symbol': '◈',
        'ascii': '>|<',
        'color': 'blue',
        'description': 'Sub-groups merging'
    },
    'scattered': {
        'symbol': '✦',
        'ascii': '...',
        'color': 'red',
        'description': 'Swarm has lost cohesion'
    },
    'circling': {
        'symbol': '↻',
        'ascii': '@',
        'color': 'purple',
        'description': 'Circular dependency detected'
    }
}
```

### Swarm Density Visualization
```python
DENSITY_INDICATORS = {
    'sparse':  {'display': '·   ·   ·', 'color': 'dim'},
    'light':   {'display': '··  ··  ··', 'color': 'normal'},
    'medium':  {'display': '··· ··· ···', 'color': 'bright'},
    'dense':   {'display': '████████', 'color': 'bold'},
    'critical': {'display': '▓▓▓▓▓▓▓▓', 'color': 'reverse'},
}
```

### Multi-Agent Activity Visualization
```python
class SwarmVisualizer:
    """Visualize swarm behavior in terminal"""

    def render_swarm_header(self, swarm_id: str, agent_count: int, pattern: str):
        """Render swarm identification header"""
        pattern_info = SWARM_PATTERNS[pattern]
        return f"{pattern_info['symbol']} Swarm [{swarm_id}] | {agent_count} agents | {pattern_info['description']}"

    def render_agent_grid(self, agents: list, width: int = 80):
        """Render grid view of agent states"""
        symbols = []
        for agent in agents:
            status = STATUS_INDICATORS[agent.status]
            color_code = agent.assigned_color['code']
            symbols.append(f"\033[38;5;{color_code}m{status['symbol']}\033[0m")

        # Arrange in grid
        grid_lines = []
        for i in range(0, len(symbols), width//2):
            grid_lines.append(' '.join(symbols[i:i+width//2]))
        return '\n'.join(grid_lines)

    def render_communication_flow(self, messages: list):
        """Visualize inter-agent communication"""
        flow_template = "{sender_color}{sender}{reset} → {receiver_color}{receiver}{reset}: {msg_type}"
        # Implementation details...
```

## Terminal Compatibility Guidelines

### Feature Detection
```python
class TerminalCapabilities:
    """Detect and adapt to terminal capabilities"""

    @staticmethod
    def detect():
        capabilities = {
            'colors': TerminalCapabilities._detect_colors(),
            'unicode': TerminalCapabilities._detect_unicode(),
            'emoji': TerminalCapabilities._detect_emoji(),
            'size': TerminalCapabilities._get_terminal_size(),
        }
        return capabilities

    @staticmethod
    def _detect_colors():
        """Detect color support level"""
        import os

        # Check NO_COLOR environment variable
        if os.environ.get('NO_COLOR'):
            return 0

        # Check TERM variable
        term = os.environ.get('TERM', '')
        if 'dumb' in term:
            return 0
        elif '256color' in term:
            return 256
        elif 'color' in term:
            return 16

        # Try tput
        try:
            import subprocess
            result = subprocess.run(['tput', 'colors'],
                                  capture_output=True, text=True)
            return int(result.stdout.strip())
        except:
            return 8  # Safe default
```

### Fallback Strategies
```python
FALLBACK_MODES = {
    'no_color': {
        'agent_prefix': '[Agent-{id}]',
        'status_format': '[{status}]',
        'role_format': '<{role}>',
        'separator': ' | ',
    },
    'basic_color': {
        'colors': ['red', 'green', 'yellow', 'blue', 'magenta', 'cyan'],
        'bold_for_emphasis': True,
        'underline_for_links': True,
    },
    'ascii_only': {
        'success': '[OK]',
        'error': '[ERR]',
        'warning': '[WRN]',
        'info': '[INF]',
        'running': '[>>>]',
        'stopped': '[---]',
    }
}
```

### Responsive Design
```python
class ResponsiveFormatter:
    """Adapt output to terminal width"""

    def __init__(self, width: int = 80):
        self.width = width
        self.compact_mode = width < 80
        self.ultra_compact = width < 60

    def format_agent_line(self, agent_data: dict) -> str:
        if self.ultra_compact:
            # Minimal format: ID + Status only
            return f"{agent_data['id'][:8]} {agent_data['status_icon']}"
        elif self.compact_mode:
            # Compact: ID + Role + Status
            return f"{agent_data['id'][:12]} {agent_data['role_icon']} {agent_data['status_icon']}"
        else:
            # Full format
            return f"{agent_data['id']} {agent_data['role']} {agent_data['status']} {agent_data['message']}"
```

## Implementation Examples

### Basic Usage
```python
from visual_design import AgentColorAssigner, TerminalCapabilities

# Initialize
capabilities = TerminalCapabilities.detect()
color_scheme = 'colorblind_safe' if capabilities['colors'] >= 256 else 'basic'
assigner = AgentColorAssigner(scheme=color_scheme)

# Assign colors to agents
for agent_id in agent_ids:
    color = assigner.assign_color(agent_id)
    print(f"\033[38;5;{color['code']}m[{agent_id}]\033[0m Starting...")
```

### Advanced Swarm Visualization
```python
visualizer = SwarmVisualizer()

# Render swarm state
header = visualizer.render_swarm_header("swarm-001", 15, "forming")
grid = visualizer.render_agent_grid(agents)
print(header)
print(grid)
```

## Performance Optimization

### Color Caching
```python
class ColorCache:
    """Cache formatted strings to avoid repeated ANSI code generation"""

    def __init__(self):
        self._cache = {}

    def get_colored(self, text: str, color_code: int, style: str = '') -> str:
        cache_key = (text, color_code, style)
        if cache_key not in self._cache:
            style_code = {'bold': '1;', 'dim': '2;', 'italic': '3;'}.get(style, '')
            self._cache[cache_key] = f"\033[{style_code}38;5;{color_code}m{text}\033[0m"
        return self._cache[cache_key]
```

### Batch Rendering
```python
def batch_render_agents(agents: list, buffer_size: int = 1000):
    """Batch render to minimize system calls"""
    buffer = []
    for agent in agents:
        line = format_agent_line(agent)
        buffer.append(line)
        if len(buffer) >= buffer_size:
            print('\n'.join(buffer))
            buffer = []
    if buffer:
        print('\n'.join(buffer))
```

## Testing & Validation

### Color Contrast Testing
```python
def test_color_contrast(fg_color: tuple, bg_color: tuple = (0, 0, 0)) -> float:
    """Calculate WCAG contrast ratio"""
    def relative_luminance(color):
        r, g, b = [c/255.0 for c in color]
        r = r/12.92 if r <= 0.03928 else ((r+0.055)/1.055)**2.4
        g = g/12.92 if g <= 0.03928 else ((g+0.055)/1.055)**2.4
        b = b/12.92 if b <= 0.03928 else ((b+0.055)/1.055)**2.4
        return 0.2126*r + 0.7152*g + 0.0722*b

    l1 = relative_luminance(fg_color)
    l2 = relative_luminance(bg_color)
    return (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05)
```

### Terminal Compatibility Matrix
```
Terminal         | 256-Color | Unicode | Emoji | True Color
-----------------|-----------|---------|-------|------------
Linux (modern)   | ✓         | ✓       | ✓     | ✓
macOS Terminal   | ✓         | ✓       | ✓     | ✓
Windows Terminal | ✓         | ✓       | ✓     | ✓
iTerm2          | ✓         | ✓       | ✓     | ✓
VS Code         | ✓         | ✓       | ✓     | ✓
tmux            | ✓         | ✓       | ◐     | ◐
screen          | ◐         | ✓       | ✗     | ✗
TTY/Console     | ✗         | ◐       | ✗     | ✗
```

## Quick Reference

### Environment Variables
```bash
# Force color mode
export FORCE_COLOR=1
export COLORTERM=truecolor

# Disable colors
export NO_COLOR=1

# Set color scheme
export AGENT_COLOR_SCHEME=colorblind_safe
export AGENT_USE_EMOJI=0
```

### Command Line Flags
```
--color=auto|always|never    Color output control
--color-scheme=default|high_contrast|colorblind_safe
--no-emoji                   Disable emoji output
--compact                    Use compact display mode
--ascii-only                 Use ASCII characters only
```

## Summary

This visual design system provides:
1. **Comprehensive color palette** with 256-color and fallback options
2. **Intelligent agent color assignment** with uniqueness guarantees
3. **Rich role and status indicators** with emoji and ASCII alternatives
4. **Advanced swarm visualization** for multi-agent behavior
5. **Full terminal compatibility** with automatic capability detection
6. **Accessibility-first approach** with colorblind-safe options
7. **Performance optimizations** for real-time monitoring

The system ensures high contrast, accessibility, and graceful degradation across all terminal environments while providing rich visual feedback for complex agent orchestration scenarios.

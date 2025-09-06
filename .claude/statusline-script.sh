#!/bin/bash

# Advanced Claude Code Status Line
# Features: Git status, project context, model info, system stats, and visual indicators

# Read Claude Code JSON input
input=$(cat)

# Extract data from JSON input
model_name=$(echo "$input" | jq -r '.model.display_name // "Claude"')
model_id=$(echo "$input" | jq -r '.model.id // ""')
current_dir=$(echo "$input" | jq -r '.workspace.current_dir // ""')
project_dir=$(echo "$input" | jq -r '.workspace.project_dir // ""')
output_style=$(echo "$input" | jq -r '.output_style.name // "default"')
version=$(echo "$input" | jq -r '.version // ""')

# Color codes (dimmed for status line)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[0;37m'
GRAY='\033[0;90m'
BOLD='\033[1m'
DIM='\033[2m'
RESET='\033[0m'

# Unicode symbols
BRANCH_SYMBOL="⎇"
AHEAD_SYMBOL="↑"
BEHIND_SYMBOL="↓"
MODIFIED_SYMBOL="●"
STAGED_SYMBOL="✓"
UNTRACKED_SYMBOL="?"
STASH_SYMBOL="⚑"
LIGHTNING_SYMBOL="⚡"
ROCKET_SYMBOL="🚀"
BRAIN_SYMBOL="🧠"
FOLDER_SYMBOL="📁"
TIME_SYMBOL="⏰"
PYTHON_SYMBOL="🐍"
DOCKER_SYMBOL="🐳"

# Get current time
current_time=$(date +"%H:%M:%S")

# Get git information if in a git repository
git_info=""
if git rev-parse --git-dir > /dev/null 2>&1; then
    # Get current branch
    branch=$(git symbolic-ref --short HEAD 2>/dev/null || git rev-parse --short HEAD 2>/dev/null || "unknown")
    
    # Get git status info
    git_status=$(git status --porcelain 2>/dev/null)
    modified_count=$(echo "$git_status" | grep -c "^ M\|^M " 2>/dev/null || echo "0")
    staged_count=$(echo "$git_status" | grep -c "^M\|^A\|^D\|^R\|^C" 2>/dev/null || echo "0")
    untracked_count=$(echo "$git_status" | grep -c "^??" 2>/dev/null || echo "0")
    
    # Get ahead/behind info
    ahead_behind=$(git rev-list --count --left-right @{upstream}...HEAD 2>/dev/null)
    if [[ -n "$ahead_behind" ]]; then
        behind=$(echo "$ahead_behind" | cut -f1)
        ahead=$(echo "$ahead_behind" | cut -f2)
    else
        behind=0
        ahead=0
    fi
    
    # Check for stashes
    stash_count=$(git stash list 2>/dev/null | wc -l | tr -d ' ')
    
    # Build git status string
    git_indicators=""
    [[ $modified_count -gt 0 ]] && git_indicators="${git_indicators}${YELLOW}${MODIFIED_SYMBOL}${modified_count}${RESET}"
    [[ $staged_count -gt 0 ]] && git_indicators="${git_indicators}${GREEN}${STAGED_SYMBOL}${staged_count}${RESET}"
    [[ $untracked_count -gt 0 ]] && git_indicators="${git_indicators}${RED}${UNTRACKED_SYMBOL}${untracked_count}${RESET}"
    [[ $ahead -gt 0 ]] && git_indicators="${git_indicators}${BLUE}${AHEAD_SYMBOL}${ahead}${RESET}"
    [[ $behind -gt 0 ]] && git_indicators="${git_indicators}${PURPLE}${BEHIND_SYMBOL}${behind}${RESET}"
    [[ $stash_count -gt 0 ]] && git_indicators="${git_indicators}${CYAN}${STASH_SYMBOL}${stash_count}${RESET}"
    
    git_info="${GRAY}${BRANCH_SYMBOL}${RESET} ${GREEN}${branch}${RESET}"
    [[ -n "$git_indicators" ]] && git_info="${git_info} ${git_indicators}"
fi

# Get project context
project_info=""
if [[ -n "$project_dir" && "$project_dir" != "null" ]]; then
    project_name=$(basename "$project_dir")
    
    # Detect project type
    project_type=""
    if [[ -f "$project_dir/pyproject.toml" || -f "$project_dir/requirements.txt" || -f "$project_dir/setup.py" ]]; then
        project_type="${PYTHON_SYMBOL} Python"
    elif [[ -f "$project_dir/package.json" ]]; then
        project_type="📦 Node.js"
    elif [[ -f "$project_dir/Dockerfile" ]]; then
        project_type="${DOCKER_SYMBOL} Docker"
    elif [[ -f "$project_dir/Cargo.toml" ]]; then
        project_type="🦀 Rust"
    elif [[ -f "$project_dir/go.mod" ]]; then
        project_type="🐹 Go"
    fi
    
    project_info="${FOLDER_SYMBOL} ${BOLD}${project_name}${RESET}"
    [[ -n "$project_type" ]] && project_info="${project_info} ${DIM}${project_type}${RESET}"
fi

# Get system info
load_avg=$(uptime | grep -o 'load average: [0-9.,]*' | cut -d' ' -f3 | cut -d',' -f1)
memory_usage=$(free | grep Mem | awk '{printf "%.0f%%", $3/$2 * 100.0}')

# Build model info with smart truncation
model_display="$model_name"
if [[ "$model_id" == *"sonnet"* ]]; then
    model_display="${BRAIN_SYMBOL} ${model_display}"
elif [[ "$model_id" == *"haiku"* ]]; then
    model_display="🎋 ${model_display}"
elif [[ "$model_id" == *"opus"* ]]; then
    model_display="🎭 ${model_display}"
else
    model_display="${LIGHTNING_SYMBOL} ${model_display}"
fi

# Build output style indicator
style_indicator=""
case "$output_style" in
    "Explanatory") style_indicator="${BLUE}📚 Explain${RESET}" ;;
    "Learning") style_indicator="${GREEN}🎓 Learn${RESET}" ;;
    "Concise") style_indicator="${YELLOW}⚡ Brief${RESET}" ;;
    "Creative") style_indicator="${PURPLE}🎨 Creative${RESET}" ;;
    *) style_indicator="${GRAY}${output_style}${RESET}" ;;
esac

# Assemble the final status line
status_parts=()

# Time and system info
status_parts+=("${DIM}${TIME_SYMBOL} ${current_time}${RESET}")
status_parts+=("${DIM}⚙️ ${load_avg} ${memory_usage}${RESET}")

# Model and style
status_parts+=("${CYAN}${model_display}${RESET}")
[[ -n "$style_indicator" ]] && status_parts+=("${style_indicator}")

# Project context
[[ -n "$project_info" ]] && status_parts+=("${project_info}")

# Git information
[[ -n "$git_info" ]] && status_parts+=("${git_info}")

# Working directory (abbreviated)
if [[ -n "$current_dir" && "$current_dir" != "null" ]]; then
    # Abbreviate long paths
    short_dir="$current_dir"
    if [[ ${#current_dir} -gt 40 ]]; then
        short_dir="...${current_dir: -37}"
    fi
    status_parts+=("${DIM}📍 ${short_dir}${RESET}")
fi

# Join all parts with separators
separator="${DIM} │ ${RESET}"
final_status=""
for i in "${!status_parts[@]}"; do
    if [[ $i -eq 0 ]]; then
        final_status="${status_parts[$i]}"
    else
        final_status="${final_status}${separator}${status_parts[$i]}"
    fi
done

# Output the final status line
printf "%b\n" "$final_status"
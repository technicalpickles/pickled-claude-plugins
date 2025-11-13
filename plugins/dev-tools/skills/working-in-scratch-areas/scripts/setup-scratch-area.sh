#!/usr/bin/env bash

# setup-scratch-area.sh
#
# Purpose: Sets up a scratch area for the current repository by:
# 1. Determining scratch areas root location (from CLAUDE.md or via --areas-root flag)
# 2. Creating a subdirectory matching the repository name
# 3. Creating a symlink from .scratch in the repository root to the created subdirectory
#
# Usage: Run this script from within any repository directory
# Examples:
#   ./setup-scratch-area.sh --areas-root ~/workspace/scratch-areas
#   ./setup-scratch-area.sh --areas-root ~/workspace/scratch-areas --save-to-claude-md
#
# Options:
#   --areas-root PATH       Specify scratch areas root directory (required if not in CLAUDE.md)
#   --save-to-claude-md     Save the areas root to ~/.claude/CLAUDE.md for future use
#   --help                  Show this help message
#
# This script follows the scratch area convention where one-off scripts and
# documentation are saved to a .scratch directory that symlinks to a
# centralized location for easy access and organization.

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Parse command line arguments
AREAS_ROOT_ARG=""
SAVE_TO_CLAUDE_MD=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --areas-root)
            AREAS_ROOT_ARG="$2"
            shift 2
            ;;
        --save-to-claude-md)
            SAVE_TO_CLAUDE_MD=true
            shift
            ;;
        --help)
            echo "Usage: setup-scratch-area.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --areas-root PATH       Specify scratch areas root directory"
            echo "  --save-to-claude-md     Save the areas root to ~/.claude/CLAUDE.md"
            echo "  --help                  Show this help message"
            echo ""
            echo "Examples:"
            echo "  ./setup-scratch-area.sh --areas-root ~/workspace/scratch-areas"
            echo "  ./setup-scratch-area.sh --areas-root ~/workspace/scratch-areas --save-to-claude-md"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    print_error "Not in a git repository. Please run this script from within a git repository."
    exit 1
fi

# Get the repository name and root
REPO_NAME=$(basename "$(git rev-parse --show-toplevel)")
REPO_ROOT="$(git rev-parse --show-toplevel)"
print_status "Repository name: $REPO_NAME"
print_status "Repository root: $REPO_ROOT"

# Define script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Determine areas root location
CLAUDE_MD="$HOME/.claude/CLAUDE.md"
AREAS_ROOT=""

# Priority: CLI argument > CLAUDE.md
if [ -n "$AREAS_ROOT_ARG" ]; then
    AREAS_ROOT="$AREAS_ROOT_ARG"
elif [ -f "$CLAUDE_MD" ]; then
    AREAS_ROOT=$(grep -i "^[[:space:]]*scratch areas:" "$CLAUDE_MD" | head -1 | sed 's/^[[:space:]]*[Ss]cratch areas:[[:space:]]*//' | sed 's/[[:space:]]*directory[[:space:]]*$//' | sed 's/`//g')
fi

# If still not set, error
if [ -z "$AREAS_ROOT" ]; then
    print_error "Scratch areas location not specified and not found in ~/.claude/CLAUDE.md"
    echo ""
    echo "Please provide --areas-root flag or configure in ~/.claude/CLAUDE.md:"
    echo ""
    echo "  ## Scratch Areas"
    echo ""
    echo "  When using the \`dev-tools:working-in-scratch-areas\` skill, create scratch areas in \`/your/path\` directory."
    echo ""
    echo "Example usage:"
    echo "  ./setup-scratch-area.sh --areas-root ~/workspace/scratch-areas"
    exit 1
fi

# Save to CLAUDE.md if requested
if [ "$SAVE_TO_CLAUDE_MD" = true ]; then
    # Create CLAUDE.md if it doesn't exist
    if [ ! -f "$CLAUDE_MD" ]; then
        mkdir -p "$(dirname "$CLAUDE_MD")"
        touch "$CLAUDE_MD"
    fi

    # Check if Scratch Areas section already exists
    if grep -q "^## Scratch Areas" "$CLAUDE_MD"; then
        print_warning "Scratch Areas section already exists in CLAUDE.md"
        print_status "Please update it manually to: Scratch areas: $AREAS_ROOT"
    else
        echo "" >> "$CLAUDE_MD"
        echo "## Scratch Areas" >> "$CLAUDE_MD"
        echo "" >> "$CLAUDE_MD"
        echo "When using the \`dev-tools:working-in-scratch-areas\` skill, create scratch areas in \`$AREAS_ROOT\` directory." >> "$CLAUDE_MD"
        print_success "Saved to ~/.claude/CLAUDE.md"
    fi
fi

# Expand tilde in AREAS_ROOT if present
AREAS_ROOT="${AREAS_ROOT/#\~/$HOME}"

REPO_SCRATCH_DIR="$AREAS_ROOT/$REPO_NAME"
SCRATCH_AREA_LINK="$REPO_ROOT/.scratch"

print_status "Scratch areas root: $AREAS_ROOT"
print_status "Target scratch directory: $REPO_SCRATCH_DIR"
print_status "Symlink location: $SCRATCH_AREA_LINK"

# Check if areas root exists, create if not
if [ ! -d "$AREAS_ROOT" ]; then
    print_status "Creating scratch areas root directory..."
    if ! mkdir -p "$AREAS_ROOT"; then
        print_error "Failed to create scratch areas root directory: $AREAS_ROOT"
        exit 1
    fi
    print_success "Created $AREAS_ROOT"
fi

# Check if repository-specific scratch directory exists, create if not
if [ ! -d "$REPO_SCRATCH_DIR" ]; then
    print_status "Creating repository scratch directory..."
    if ! mkdir -p "$REPO_SCRATCH_DIR"; then
        print_error "Failed to create repository scratch directory: $REPO_SCRATCH_DIR"
        exit 1
    fi
    print_success "Created $REPO_SCRATCH_DIR"
else
    print_status "Repository scratch directory already exists: $REPO_SCRATCH_DIR"
fi

# Check if .scratch already exists and handle different cases
if [ -L "$SCRATCH_AREA_LINK" ]; then
    print_warning "Symlink already exists at $SCRATCH_AREA_LINK"

    # Check if it points to the correct location
    LINK_TARGET=$(readlink "$SCRATCH_AREA_LINK")
    if [ "$LINK_TARGET" = "$REPO_SCRATCH_DIR" ]; then
        print_success "Symlink already points to the correct location"
        exit 0
    else
        print_warning "Symlink points to: $LINK_TARGET"
        print_warning "Expected: $REPO_SCRATCH_DIR"
        print_error "Symlink points to wrong location. Please remove it manually and run again:"
        print_error "  rm $SCRATCH_AREA_LINK"
        exit 1
    fi
elif [ -d "$SCRATCH_AREA_LINK" ]; then
    print_warning "Found existing .scratch directory at $SCRATCH_AREA_LINK"

    # Check if the directory has any files
    if [ -z "$(ls -A "$SCRATCH_AREA_LINK" 2>/dev/null)" ]; then
        print_status "Directory is empty, removing it..."
        rmdir "$SCRATCH_AREA_LINK"
    else
        print_status "Directory contains files, moving them to centralized location..."

        # Check if there are any conflicts in the target directory
        CONFLICTS=()
        for item in "$SCRATCH_AREA_LINK"/*; do
            if [ -e "$item" ]; then
                BASENAME=$(basename "$item")
                if [ -e "$REPO_SCRATCH_DIR/$BASENAME" ]; then
                    CONFLICTS+=("$BASENAME")
                fi
            fi
        done

        if [ ${#CONFLICTS[@]} -gt 0 ]; then
            print_error "Conflicts detected in target directory:"
            for conflict in "${CONFLICTS[@]}"; do
                print_error "  - $conflict"
            done
            print_error "Please resolve conflicts manually and run the script again"
            exit 1
        fi

        # Move all files from the .scratch directory to the centralized location
        print_status "Moving files from $SCRATCH_AREA_LINK to $REPO_SCRATCH_DIR"

        # Move regular files
        if ! mv "$SCRATCH_AREA_LINK"/* "$REPO_SCRATCH_DIR/" 2>/dev/null; then
            print_warning "No regular files to move or failed to move some files"
        fi

        # Move hidden files (but not . and ..)
        if ! mv "$SCRATCH_AREA_LINK"/.[!.]* "$REPO_SCRATCH_DIR/" 2>/dev/null; then
            print_warning "No hidden files to move or failed to move some files"
        fi

        # Remove the now-empty directory
        if ! rmdir "$SCRATCH_AREA_LINK"; then
            print_error "Failed to remove empty .scratch directory"
            exit 1
        fi
        print_success "Moved files and removed empty directory"
    fi
elif [ -e "$SCRATCH_AREA_LINK" ]; then
    print_error "A file named '.scratch' already exists at $SCRATCH_AREA_LINK"
    print_error "Please remove it manually and run this script again"
    exit 1
fi

# Check if old scratch symlink exists and handle migration
OLD_SCRATCH_LINK="$REPO_ROOT/scratch"
if [ -L "$OLD_SCRATCH_LINK" ]; then
    print_warning "Found old scratch symlink, migrating to .scratch..."

    # Check if it points to the correct location
    OLD_LINK_TARGET=$(readlink "$OLD_SCRATCH_LINK")
    if [ "$OLD_LINK_TARGET" = "$REPO_SCRATCH_DIR" ]; then
        print_status "Old symlink points to correct location, renaming..."
        if mv "$OLD_SCRATCH_LINK" "$SCRATCH_AREA_LINK"; then
            print_success "Successfully renamed scratch to .scratch"
            exit 0
        else
            print_error "Failed to rename symlink"
            exit 1
        fi
    else
        print_warning "Old symlink points to: $OLD_LINK_TARGET"
        print_warning "Expected: $REPO_SCRATCH_DIR"
        print_error "Old symlink points to wrong location. Please remove it manually and run again:"
        print_error "  rm $OLD_SCRATCH_LINK"
        exit 1
    fi
elif [ -d "$OLD_SCRATCH_LINK" ]; then
    print_warning "Found old scratch directory, migrating to .scratch..."

    # Check if the directory has any files
    if [ -z "$(ls -A "$OLD_SCRATCH_LINK" 2>/dev/null)" ]; then
        print_status "Directory is empty, removing it..."
        rmdir "$OLD_SCRATCH_LINK"
    else
        print_status "Directory contains files, moving them to centralized location..."

        # Check if there are any conflicts in the target directory
        CONFLICTS=()
        for item in "$OLD_SCRATCH_LINK"/*; do
            if [ -e "$item" ]; then
                BASENAME=$(basename "$item")
                if [ -e "$REPO_SCRATCH_DIR/$BASENAME" ]; then
                    CONFLICTS+=("$BASENAME")
                fi
            fi
        done

        if [ ${#CONFLICTS[@]} -gt 0 ]; then
            print_error "Conflicts detected in target directory:"
            for conflict in "${CONFLICTS[@]}"; do
                print_error "  - $conflict"
            done
            print_error "Please resolve conflicts manually and run the script again"
            exit 1
        fi

        # Move all files from the old scratch directory to the centralized location
        print_status "Moving files from $OLD_SCRATCH_LINK to $REPO_SCRATCH_DIR"

        # Move regular files
        if ! mv "$OLD_SCRATCH_LINK"/* "$REPO_SCRATCH_DIR/" 2>/dev/null; then
            print_warning "No regular files to move or failed to move some files"
        fi

        # Move hidden files (but not . and ..)
        if ! mv "$OLD_SCRATCH_LINK"/.[!.]* "$REPO_SCRATCH_DIR/" 2>/dev/null; then
            print_warning "No hidden files to move or failed to move some files"
        fi

        # Remove the now-empty directory
        if ! rmdir "$OLD_SCRATCH_LINK"; then
            print_error "Failed to remove empty scratch directory"
            exit 1
        fi
        print_success "Moved files and removed empty directory"
    fi
fi

# Check if old scratch-area symlink exists and handle migration
OLD_SCRATCH_AREA_LINK="$REPO_ROOT/scratch-area"
if [ -L "$OLD_SCRATCH_AREA_LINK" ]; then
    print_warning "Found old scratch-area symlink, migrating to .scratch..."

    # Check if it points to the correct location
    OLD_LINK_TARGET=$(readlink "$OLD_SCRATCH_AREA_LINK")
    if [ "$OLD_LINK_TARGET" = "$REPO_SCRATCH_DIR" ]; then
        print_status "Old symlink points to correct location, renaming..."
        if mv "$OLD_SCRATCH_AREA_LINK" "$SCRATCH_AREA_LINK"; then
            print_success "Successfully renamed scratch-area to .scratch"
            exit 0
        else
            print_error "Failed to rename symlink"
            exit 1
        fi
    else
        print_warning "Old symlink points to: $OLD_LINK_TARGET"
        print_warning "Expected: $REPO_SCRATCH_DIR"
        print_error "Old symlink points to wrong location. Please remove it manually and run again:"
        print_error "  rm $OLD_SCRATCH_AREA_LINK"
        exit 1
    fi
elif [ -d "$OLD_SCRATCH_AREA_LINK" ]; then
    print_warning "Found old scratch-area directory, migrating to .scratch..."

    # Check if the directory has any files
    if [ -z "$(ls -A "$OLD_SCRATCH_AREA_LINK" 2>/dev/null)" ]; then
        print_status "Directory is empty, removing it..."
        rmdir "$OLD_SCRATCH_AREA_LINK"
    else
        print_status "Directory contains files, moving them to centralized location..."

        # Check if there are any conflicts in the target directory
        CONFLICTS=()
        for item in "$OLD_SCRATCH_AREA_LINK"/*; do
            if [ -e "$item" ]; then
                BASENAME=$(basename "$item")
                if [ -e "$REPO_SCRATCH_DIR/$BASENAME" ]; then
                    CONFLICTS+=("$BASENAME")
                fi
            fi
        done

        if [ ${#CONFLICTS[@]} -gt 0 ]; then
            print_error "Conflicts detected in target directory:"
            for conflict in "${CONFLICTS[@]}"; do
                print_error "  - $conflict"
            done
            print_error "Please resolve conflicts manually and run the script again"
            exit 1
        fi

        # Move all files from the old scratch-area directory to the centralized location
        print_status "Moving files from $OLD_SCRATCH_AREA_LINK to $REPO_SCRATCH_DIR"

        # Move regular files
        if ! mv "$OLD_SCRATCH_AREA_LINK"/* "$REPO_SCRATCH_DIR/" 2>/dev/null; then
            print_warning "No regular files to move or failed to move some files"
        fi

        # Move hidden files (but not . and ..)
        if ! mv "$OLD_SCRATCH_AREA_LINK"/.[!.]* "$REPO_SCRATCH_DIR/" 2>/dev/null; then
            print_warning "No hidden files to move or failed to move some files"
        fi

        # Remove the now-empty directory
        if ! rmdir "$OLD_SCRATCH_AREA_LINK"; then
            print_error "Failed to remove empty scratch-area directory"
            exit 1
        fi
        print_success "Moved files and removed empty directory"
    fi
fi

# Create the symlink
print_status "Creating symlink from $SCRATCH_AREA_LINK to $REPO_SCRATCH_DIR"
if ! ln -s "$REPO_SCRATCH_DIR" "$SCRATCH_AREA_LINK"; then
    print_error "Failed to create symlink from $SCRATCH_AREA_LINK to $REPO_SCRATCH_DIR"
    exit 1
fi

# Verify the symlink was created correctly
if [ -L "$SCRATCH_AREA_LINK" ] && [ "$(readlink "$SCRATCH_AREA_LINK")" = "$REPO_SCRATCH_DIR" ]; then
    print_success "Successfully created .scratch symlink!"
    print_success "You can now use the .scratch directory for one-off scripts and documentation"
    print_status "Scratch area location: $REPO_SCRATCH_DIR"
else
    print_error "Failed to create symlink correctly"
    exit 1
fi

# Create a README in the scratch area if it doesn't exist
README_FILE="$REPO_SCRATCH_DIR/README.md"
if [ ! -f "$README_FILE" ]; then
    # Check multiple template locations
    # 1. Skill location (../templates/ from scripts/)
    SKILL_TEMPLATE="$SCRIPT_DIR/../templates/scratch-area-readme-template.md"
    # 2. Original repo location (./templates/ from script root)
    REPO_TEMPLATE="$SCRIPT_DIR/templates/scratch-area-readme-template.md"

    TEMPLATE_FILE=""
    if [ -f "$SKILL_TEMPLATE" ]; then
        TEMPLATE_FILE="$SKILL_TEMPLATE"
    elif [ -f "$REPO_TEMPLATE" ]; then
        TEMPLATE_FILE="$REPO_TEMPLATE"
    fi

    if [ -z "$TEMPLATE_FILE" ]; then
        print_warning "README template not found. Skipping README creation."
        print_status "You can create a README manually in: $REPO_SCRATCH_DIR"
    else
        # Copy and customize the template
        print_status "Creating README.md from template..."
        sed -e "s/{{REPO_NAME}}/$REPO_NAME/g" \
            -e "s|{{REPO_SCRATCH_DIR}}|$REPO_SCRATCH_DIR|g" \
            -e "s|{{REPO_ROOT}}|$REPO_ROOT|g" \
            "$TEMPLATE_FILE" > "$README_FILE"

        print_success "Created README.md in scratch area"
    fi
fi

print_success "Scratch area setup complete!"

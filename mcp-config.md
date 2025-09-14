# Git MCP Server Configuration Guide

## 🚀 Git MCP Servers Installed

I've installed two Git MCP servers for you:

1. **`@cyanheads/git-mcp-server`** (v2.3.2) - Comprehensive Git operations
2. **`mcp-git`** (v0.0.4) - Basic Git MCP server

## 🔧 How to Connect Git MCP in Claude Code

### Option 1: Configure via Claude Code Settings

1. **Open Claude Code Settings**
   - Press `Ctrl+,` (or `Cmd+,` on Mac)
   - Go to MCP Servers section

2. **Add Git MCP Server Configuration**
   Add this configuration:

```json
{
  "mcpServers": {
    "git": {
      "command": "npx",
      "args": ["@cyanheads/git-mcp-server"],
      "env": {
        "GIT_MCP_WORKSPACE": "E:/Aethon_draft/Enricher/cyberpunk-tests"
      }
    }
  }
}
```

### Option 2: Manual MCP Configuration File

Create or update your MCP configuration file (usually `~/.config/claude/mcp_servers.json`):

```json
{
  "mcpServers": {
    "git-comprehensive": {
      "command": "npx",
      "args": ["@cyanheads/git-mcp-server"],
      "env": {
        "GIT_MCP_WORKSPACE": "E:/Aethon_draft/Enricher/cyberpunk-tests"
      }
    },
    "git-basic": {
      "command": "npx", 
      "args": ["mcp-git"],
      "env": {
        "GIT_REPO_PATH": "E:/Aethon_draft/Enricher/cyberpunk-tests"
      }
    }
  }
}
```

### Option 3: Test MCP Server Directly

Test if the server works:

```bash
# Test the comprehensive git server
npx @cyanheads/git-mcp-server

# Test basic git server  
npx mcp-git
```

## 🛠 Available Git Operations

Once connected, you'll have access to these Git operations via MCP:

### Basic Operations
- `git_status` - Check repository status
- `git_add` - Stage files
- `git_commit` - Create commits
- `git_push` - Push to remote
- `git_pull` - Pull from remote
- `git_log` - View commit history

### Advanced Operations
- `git_branch` - Branch operations
- `git_merge` - Merge branches
- `git_rebase` - Rebase operations
- `git_diff` - View differences
- `git_clone` - Clone repositories
- `git_tag` - Tag management
- `git_stash` - Stash operations
- `git_worktree` - Worktree management

## 🔍 Testing the Connection

Once configured, test the MCP connection:

1. **In Claude Code, try using:**
   - `@git status` - Should show current repository status
   - `@git log --oneline -5` - Should show recent commits
   - `@git branch` - Should show available branches

2. **Verify the tools are available:**
   The Git MCP tools should appear in your available tools list

## 🚨 Troubleshooting

### Common Issues:

**1. Command not found**
```bash
# Verify installation
npm list -g @cyanheads/git-mcp-server
npm list -g mcp-git
```

**2. Permission issues**
```bash
# Check if you can run the servers
npx @cyanheads/git-mcp-server --help
```

**3. Path issues**
- Make sure the workspace path is correct: `E:/Aethon_draft/Enricher/cyberpunk-tests`
- Verify the git repository exists in that path

### Re-installation if needed:
```bash
npm uninstall -g @cyanheads/git-mcp-server mcp-git
npm install -g @cyanheads/git-mcp-server mcp-git
```

## 📊 Current Repository Status

Your current repository is ready:
- **Location:** `E:/Aethon_draft/Enricher/cyberpunk-tests`
- **Branch:** `master`  
- **Status:** Clean working tree
- **Files:** 21 committed files
- **Ready for:** Push to GitHub

## 🎯 Next Steps

1. **Configure the MCP server** in Claude Code settings
2. **Test the connection** with `@git status` 
3. **Use Git MCP tools** for advanced Git operations
4. **Push to GitHub** using MCP or manual commands

Once connected, you'll be able to use Git operations directly through Claude Code's MCP interface!
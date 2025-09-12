#!/usr/bin/env node

/**
 * Test script for Git MCP server functionality
 * This script will test if the Git MCP server is working correctly
 */

const { spawn } = require('child_process');
const path = require('path');

async function testMcpServer() {
    console.log('🧪 Testing Git MCP Server...\n');
    
    // Test 1: Check if @cyanheads/git-mcp-server is available
    console.log('1. Testing @cyanheads/git-mcp-server...');
    try {
        const result = await runCommand('npx', ['@cyanheads/git-mcp-server', '--help'], 5000);
        console.log('   ✅ @cyanheads/git-mcp-server is available');
    } catch (error) {
        console.log('   ❌ @cyanheads/git-mcp-server failed:', error.message);
    }
    
    // Test 2: Check if mcp-git is available  
    console.log('\n2. Testing mcp-git...');
    try {
        const result = await runCommand('npx', ['mcp-git', '--help'], 5000);
        console.log('   ✅ mcp-git is available');
    } catch (error) {
        console.log('   ❌ mcp-git failed:', error.message);
    }
    
    // Test 3: Check current git status
    console.log('\n3. Testing current git repository...');
    try {
        const status = await runCommand('git', ['status', '--porcelain'], 3000);
        console.log('   ✅ Git repository is accessible');
        console.log('   📊 Repository status:', status.trim() || 'Clean working tree');
    } catch (error) {
        console.log('   ❌ Git repository access failed:', error.message);
    }
    
    // Test 4: Show recent commits
    console.log('\n4. Recent commits:');
    try {
        const commits = await runCommand('git', ['log', '--oneline', '-3'], 3000);
        console.log('   📝 Recent commits:');
        commits.split('\n').forEach(commit => {
            if (commit.trim()) {
                console.log('      ', commit.trim());
            }
        });
    } catch (error) {
        console.log('   ❌ Could not get commit history:', error.message);
    }
    
    // Test 5: Show branch information
    console.log('\n5. Branch information:');
    try {
        const branch = await runCommand('git', ['branch', '--show-current'], 3000);
        console.log('   🌿 Current branch:', branch.trim());
        
        const allBranches = await runCommand('git', ['branch', '-a'], 3000);
        console.log('   📋 All branches:');
        allBranches.split('\n').forEach(b => {
            if (b.trim()) {
                console.log('      ', b.trim());
            }
        });
    } catch (error) {
        console.log('   ❌ Could not get branch information:', error.message);
    }
    
    console.log('\n🎯 MCP Configuration Recommendations:');
    console.log('   • Add Git MCP server to Claude Code settings');
    console.log('   • Use workspace path: I:/CYBERPUNK/tests');
    console.log('   • Test with @git commands in Claude Code');
    console.log('   • See mcp-config.md for detailed setup instructions');
}

function runCommand(command, args, timeout = 10000) {
    return new Promise((resolve, reject) => {
        const process = spawn(command, args, {
            cwd: __dirname,
            stdio: ['ignore', 'pipe', 'pipe']
        });
        
        let stdout = '';
        let stderr = '';
        
        process.stdout.on('data', (data) => {
            stdout += data.toString();
        });
        
        process.stderr.on('data', (data) => {
            stderr += data.toString();
        });
        
        const timer = setTimeout(() => {
            process.kill('SIGKILL');
            reject(new Error('Command timed out'));
        }, timeout);
        
        process.on('close', (code) => {
            clearTimeout(timer);
            if (code === 0) {
                resolve(stdout);
            } else {
                reject(new Error(`Command failed with code ${code}: ${stderr}`));
            }
        });
        
        process.on('error', (error) => {
            clearTimeout(timer);
            reject(error);
        });
    });
}

// Run the test
testMcpServer().catch(console.error);
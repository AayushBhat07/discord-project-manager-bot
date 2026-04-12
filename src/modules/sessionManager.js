const jsonfile = require('jsonfile');
const path = require('path');
const fs = require('fs');
const { v4: uuidv4 } = require('uuid');
const moment = require('moment');

class SessionManager {
  constructor() {
    this.storePath = null;
    this.sessions = new Map();
    this.retentionDays = 30;
  }

  initialize(storePath, options = {}) {
    this.storePath = storePath;
    this.retentionDays = options.retentionDays || 30;
    return this.loadSessions();
  }

  async loadSessions() {
    try {
      if (this.storePath && fs.existsSync(this.storePath)) {
        const data = await jsonfile.readFile(this.storePath);
        if (data && data.sessions) {
          for (const [id, session] of Object.entries(data.sessions)) {
            this.sessions.set(id, session);
          }
        }
        this.cleanExpiredSessions();
        return { success: true, loaded: this.sessions.size };
      }
    } catch (error) {
      console.error('Failed to load sessions:', error.message);
    }
    return { success: true, loaded: 0 };
  }

  async saveSessions() {
    if (!this.storePath) return;

    const sessionsObj = {};
    for (const [id, session] of this.sessions) {
      sessionsObj[id] = session;
    }

    try {
      const dir = path.dirname(this.storePath);
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
      await jsonfile.writeFile(this.storePath, { 
        sessions: sessionsObj, 
        updatedAt: new Date().toISOString() 
      });
    } catch (error) {
      console.error('Failed to save sessions:', error.message);
    }
  }

  createSession(userId, userName, metadata = {}) {
    const id = uuidv4();
    const now = new Date();

    const session = {
      id,
      userId,
      userName,
      startTime: now.toISOString(),
      lastActive: now.toISOString(),
      metadata: {
        repoPath: metadata.repoPath || null,
        repoRemote: metadata.repoRemote || null,
        branch: metadata.branch || 'main',
        isActive: true,
        ...metadata
      },
      commits: [],
      stats: {
        totalCommits: 0,
        backdatedCommits: 0,
        scheduledCommits: 0,
        patternCommits: 0
      }
    };

    this.sessions.set(id, session);
    this.saveSessions();

    return session;
  }

  getActiveSession(userId) {
    for (const [id, session] of this.sessions) {
      if (session.userId === userId && session.metadata.isActive) {
        return session;
      }
    }
    return null;
  }

  getSession(sessionId) {
    return this.sessions.get(sessionId) || null;
  }

  getUserSessions(userId) {
    const userSessions = [];
    for (const [id, session] of this.sessions) {
      if (session.userId === userId) {
        userSessions.push(session);
      }
    }
    return userSessions.sort((a, b) => new Date(b.startTime) - new Date(a.startTime));
  }

  updateSession(sessionId, updates) {
    const session = this.sessions.get(sessionId);
    if (!session) return null;

    session.lastActive = new Date().toISOString();
    
    if (updates.metadata) {
      session.metadata = { ...session.metadata, ...updates.metadata };
    }
    if (updates.stats) {
      session.stats = { ...session.stats, ...updates.stats };
    }

    this.sessions.set(sessionId, session);
    this.saveSessions();

    return session;
  }

  addCommitToSession(sessionId, commitData) {
    const session = this.sessions.get(sessionId);
    if (!session) return null;

    const commit = {
      id: uuidv4(),
      timestamp: commitData.timestamp || new Date().toISOString(),
      message: commitData.message,
      type: commitData.type || 'normal',
      success: commitData.success || false,
      repo: commitData.repo || session.metadata.repoPath
    };

    session.commits.push(commit);
    session.stats.totalCommits++;
    
    if (commitData.type === 'backdated') session.stats.backdatedCommits++;
    if (commitData.type === 'scheduled') session.stats.scheduledCommits++;
    if (commitData.type === 'pattern') session.stats.patternCommits++;

    this.sessions.set(sessionId, session);
    this.saveSessions();

    return commit;
  }

  endSession(sessionId) {
    const session = this.sessions.get(sessionId);
    if (!session) return null;

    session.metadata.isActive = false;
    session.endTime = new Date().toISOString();
    
    this.sessions.set(sessionId, session);
    this.saveSessions();

    return session;
  }

  cleanExpiredSessions() {
    const cutoff = moment().subtract(this.retentionDays, 'days');
    let cleaned = 0;

    for (const [id, session] of this.sessions) {
      const sessionTime = moment(session.lastActive);
      if (sessionTime.isBefore(cutoff)) {
        this.sessions.delete(id);
        cleaned++;
      }
    }

    if (cleaned > 0) {
      this.saveSessions();
      console.log(`Cleaned up ${cleaned} expired sessions`);
    }

    return cleaned;
  }

  deleteSession(sessionId) {
    const session = this.sessions.get(sessionId);
    if (!session) return { success: false, error: 'Session not found' };

    this.sessions.delete(sessionId);
    this.saveSessions();

    return { success: true, session };
  }

  getAllSessions(options = {}) {
    let sessions = Array.from(this.sessions.values());

    if (options.activeOnly) {
      sessions = sessions.filter(s => s.metadata.isActive);
    }

    if (options.userId) {
      sessions = sessions.filter(s => s.userId === options.userId);
    }

    if (options.limit) {
      sessions = sessions.slice(0, options.limit);
    }

    return sessions;
  }

  getSessionStats(userId) {
    const sessions = this.getUserSessions(userId);
    
    const totalCommits = sessions.reduce((sum, s) => sum + s.stats.totalCommits, 0);
    const backdated = sessions.reduce((sum, s) => sum + s.stats.backdatedCommits, 0);
    const scheduled = sessions.reduce((sum, s) => sum + s.stats.scheduledCommits, 0);
    const pattern = sessions.reduce((sum, s) => sum + s.stats.patternCommits, 0);
    const activeSessions = sessions.filter(s => s.metadata.isActive).length;

    return {
      totalSessions: sessions.length,
      activeSessions,
      totalCommits,
      backdatedCommits: backdated,
      scheduledCommits: scheduled,
      patternCommits: pattern,
      oldestSession: sessions.length > 0 ? sessions[sessions.length - 1].startTime : null,
      newestSession: sessions.length > 0 ? sessions[0].startTime : null
    };
  }
}

module.exports = new SessionManager();
const moment = require('moment');

class TimestampProcessor {
  constructor() {
    this.allowedFormats = [
      'YYYY-MM-DD',
      'YYYY-MM-DD HH:mm',
      'YYYY-MM-DD HH:mm:ss',
      'MM/DD/YYYY',
      'DD/MM/YYYY',
      'MMMM DD, YYYY',
      'MMMM DD YYYY',
      'YYYY/MM/DD'
    ];
    
    this.relativePatterns = {
      'yesterday': -1,
      'today': 0,
      'tomorrow': 1,
      'last week': -7,
      'next week': 7,
      'last month': -30,
      'next month': 30
    };
  }

  parse(input) {
    if (!input || typeof input !== 'string') {
      throw new Error('Invalid input: timestamp string required');
    }

    const trimmed = input.trim().toLowerCase();
    
    const relativeMatch = trimmed.match(/^(\d+)\s+(days?|weeks?|months?|hours?|minutes?)\s+ago$/);
    if (relativeMatch) {
      const value = parseInt(relativeMatch[1]);
      const unit = relativeMatch[2].replace(/s$/, '');
      return moment().subtract(value, unit);
    }

    const futureMatch = trimmed.match(/^in\s+(\d+)\s+(days?|weeks?|months?|hours?|minutes?)$/);
    if (futureMatch) {
      const value = parseInt(futureMatch[1]);
      const unit = futureMatch[2].replace(/s$/, '');
      return moment().add(value, unit);
    }

    if (this.relativePatterns[trimmed] !== undefined) {
      return moment().add(this.relativePatterns[trimmed], 'days');
    }

    const dayOfWeekMatch = trimmed.match(/^(last|next)\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)$/i);
    if (dayOfWeekMatch) {
      const direction = dayOfWeekMatch[1].toLowerCase();
      const dayName = dayOfWeekMatch[2];
      let m = moment().day(dayName);
      if (direction === 'last') {
        m = m.subtract(7, 'days');
      } else {
        if (m.isBefore(moment())) {
          m = m.add(7, 'days');
        }
      }
      return m;
    }

    let parsed = moment(trimmed, this.allowedFormats, true);
    if (!parsed.isValid()) {
      parsed = moment(trimmed);
    }

    if (!parsed.isValid()) {
      throw new Error(`Invalid date format: "${input}". Supported formats include: YYYY-MM-DD, YYYY-MM-DD HH:mm, relative dates like "3 days ago", "yesterday", "next Monday", etc.`);
    }

    return parsed;
  }

  toISOString(momentObj) {
    return momentObj.format('YYYY-MM-DDTHH:mm:ssZ');
  }

  toGitDate(momentObj) {
    return momentObj.format('YYYY-MM-DD HH:mm:ss');
  }

  validate(timestamp) {
    const parsed = this.parse(timestamp);
    const now = moment();
    
    if (parsed.isAfter(now) && parsed.diff(now, 'hours') > 24) {
      return {
        valid: false,
        error: 'Timestamps more than 24 hours in the future are not allowed unless explicitly enabled'
      };
    }
    
    const gitEpoch = moment('1970-01-01');
    if (parsed.isBefore(gitEpoch)) {
      return {
        valid: false,
        error: 'Timestamps cannot be before January 1, 1970 (Git epoch)'
      };
    }

    return { valid: true, parsed };
  }

  getWeekOffset(weekNumber) {
    return moment().subtract(52 - weekNumber, 'weeks').startOf('week');
  }

  getDateForCell(weekOffset, dayOfWeek) {
    return moment(weekOffset).add(dayOfWeek, 'days');
  }
}

module.exports = new TimestampProcessor();
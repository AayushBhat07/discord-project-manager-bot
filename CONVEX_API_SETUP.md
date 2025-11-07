# Convex API Endpoints Setup

This document describes the API endpoints your Convex backend needs to implement for the Discord bot to work.

## Required Endpoints

### 1. GET /discord/projects

Returns all active projects.

**Response:**
```json
[
  {
    "id": "project123",
    "name": "Website Redesign",
    "status": "active",
    "createdAt": "2024-01-01T00:00:00Z"
  }
]
```

---

### 2. POST /discord/tasks/recent

Returns tasks updated in the last N hours.

**Request:**
```json
{
  "hours": 12
}
```

**Response:**
```json
[
  {
    "id": "task123",
    "projectId": "project123",
    "title": "Fix login bug",
    "status": "completed",
    "priority": "HIGH",
    "assignee": {
      "id": "user123",
      "username": "john.doe",
      "email": "john@example.com",
      "discordId": "123456789012345678"
    },
    "updatedAt": "2024-01-15T10:30:00Z"
  }
]
```

---

### 3. POST /discord/stats

Returns user completion statistics for a project.

**Request:**
```json
{
  "projectId": "project123",
  "hours": 12
}
```

**Response:**
```json
[
  {
    "userId": "user123",
    "username": "john.doe",
    "completed": 5,
    "pending": 2,
    "email": "john@example.com",
    "discordId": "123456789012345678"
  }
]
```

---

### 4. POST /discord/incomplete

Returns pending/overdue tasks for a project.

**Request:**
```json
{
  "projectId": "project123"
}
```

**Response:**
```json
[
  {
    "id": "task456",
    "projectId": "project123",
    "title": "Deploy v2.0",
    "status": "in-progress",
    "priority": "URGENT",
    "dueDate": "2024-01-20T00:00:00Z",
    "assignee": {
      "id": "user456",
      "username": "sarah.m",
      "email": "sarah@example.com",
      "discordId": "987654321098765432"
    }
  }
]
```

---

### 5. POST /discord/commits

Returns recent GitHub commits for a project.

**Request:**
```json
{
  "projectId": "project123",
  "hours": 12
}
```

**Response:**
```json
[
  {
    "sha": "a1b2c3d4e5f6",
    "message": "Fix authentication bug",
    "author": "john.doe",
    "timestamp": "2h ago",
    "additions": 45,
    "deletions": 12,
    "url": "https://github.com/org/repo/commit/a1b2c3d4e5f6"
  }
]
```

---

### 6. POST /discord/link

Links a Discord user ID to a web app user account.

**Request:**
```json
{
  "discordId": "123456789012345678",
  "email": "john@example.com"
}
```

**Response:**
```json
{
  "success": true,
  "userId": "user123",
  "username": "john.doe",
  "email": "john@example.com",
  "discordId": "123456789012345678"
}
```

---

## Implementation Notes

### Error Responses

All endpoints should return appropriate HTTP status codes:

- **200** - Success
- **400** - Bad request (invalid parameters)
- **404** - Resource not found
- **500** - Server error

Error response format:
```json
{
  "error": "Error message here",
  "code": "ERROR_CODE"
}
```

### CORS Configuration

Make sure your Convex API allows requests from the bot's IP address or configure CORS appropriately.

### Authentication

If your API requires authentication, update the `APIService` class in `services/api_service.py` to include authentication headers:

```python
def _create_session(self) -> requests.Session:
    session = requests.Session()
    # Add authentication headers
    session.headers.update({
        'Authorization': f'Bearer {API_TOKEN}',
        'Content-Type': 'application/json'
    })
    # ... rest of the method
```

### Example Convex Functions

Here's a basic example of what a Convex function might look like:

```typescript
// convex/discord/projects.ts
import { query } from "./_generated/server";

export const getProjects = query({
  handler: async (ctx) => {
    const projects = await ctx.db
      .query("projects")
      .filter((q) => q.eq(q.field("status"), "active"))
      .collect();
    
    return projects.map(project => ({
      id: project._id,
      name: project.name,
      status: project.status,
      createdAt: project._creationTime
    }));
  }
});
```

```typescript
// convex/discord/tasks.ts
import { mutation } from "./_generated/server";
import { v } from "convex/values";

export const getRecentTasks = mutation({
  args: {
    hours: v.number()
  },
  handler: async (ctx, { hours }) => {
    const cutoffTime = Date.now() - (hours * 60 * 60 * 1000);
    
    const tasks = await ctx.db
      .query("tasks")
      .filter((q) => q.gte(q.field("updatedAt"), cutoffTime))
      .collect();
    
    // Join with users to get assignee info
    const tasksWithAssignees = await Promise.all(
      tasks.map(async (task) => {
        const user = task.assigneeId 
          ? await ctx.db.get(task.assigneeId)
          : null;
        
        return {
          ...task,
          assignee: user ? {
            id: user._id,
            username: user.username,
            email: user.email,
            discordId: user.discordId
          } : null
        };
      })
    );
    
    return tasksWithAssignees;
  }
});
```

### Setting Up Convex HTTP Routes

In your Convex project, set up HTTP routes in `convex/http.ts`:

```typescript
import { httpRouter } from "convex/server";
import { getProjects } from "./discord/projects";
import { getRecentTasks } from "./discord/tasks";

const http = httpRouter();

http.route({
  path: "/discord/projects",
  method: "GET",
  handler: getProjects
});

http.route({
  path: "/discord/tasks/recent",
  method: "POST",
  handler: getRecentTasks
});

// Add other routes...

export default http;
```

## Testing the API

You can test your API endpoints manually using curl:

```bash
# Test projects endpoint
curl https://benevolent-kookabura-514.convex.cloud/discord/projects

# Test recent tasks
curl -X POST https://benevolent-kookabura-514.convex.cloud/discord/tasks/recent \
  -H "Content-Type: application/json" \
  -d '{"hours": 12}'
```

Once all endpoints are implemented and returning data, the Discord bot will work correctly!

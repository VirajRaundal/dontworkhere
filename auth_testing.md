# Auth-Gated App Testing Playbook (dontworkhere.xyz)

Moderator auth uses Emergent Google OAuth + server session cookie. To test the protected
dashboard without a real Google login, seed a moderator + session directly in Mongo.

## Step 1: Create Test Moderator & Session
```
mongosh --eval "
use('test_database');
var token = 'test_session_' + Date.now();
db.moderators.insertOne({ email: 'qa.mod@example.com', name: 'QA Mod', picture: '', added_by: 'bootstrap', active: true, created_at: new Date().toISOString() });
db.user_sessions.insertOne({ session_token: token, email: 'qa.mod@example.com', expires_at: new Date(Date.now()+7*24*3600*1000).toISOString(), created_at: new Date().toISOString() });
print('Session token: ' + token);
"
```

## Step 2: Test Backend API
```
curl -X GET "$BACKEND/api/auth/me" -H "Authorization: Bearer <TOKEN>"
curl -X GET "$BACKEND/api/mod/stats" -H "Authorization: Bearer <TOKEN>"
curl -X GET "$BACKEND/api/mod/entries?status=pending" -H "Authorization: Bearer <TOKEN>"
```
Backend accepts the token via `session_token` httpOnly cookie OR `Authorization: Bearer <token>`.

## Step 3: Browser Testing
```
await page.context.add_cookies([{
  "name": "session_token", "value": "<TOKEN>",
  "domain": "<app-host>", "path": "/", "httpOnly": True, "secure": True, "sameSite": "None"
}])
await page.goto("https://<app-host>/mod/dashboard")
```

## Notes
- Bootstrap: first ever Google login becomes the founding moderator (moderators collection empty).
- Sample entries seeded via `python /app/backend/seed.py`.
- Public submissions land in `entries` with status=pending and are NOT shown publicly until approved.

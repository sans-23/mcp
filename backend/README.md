# Backend API Documentation for Frontend Development

This document outlines the REST API endpoints provided by the backend server. The API facilitates user management and interactive chat sessions with an AI agent.

**Base URL:** `http://127.0.0.1:8000/api/v1`

---

## 1. User Management Endpoints

**Purpose:** To create and manage user accounts.

### `POST /users/`
**Description:** Creates a new user in the database.
**Request Body (JSON):**
```json
{
  "username": "string",
  "password": "string"
}
```
**Response (JSON):**
```json
{
  "id": 0,
  "username": "string"
}
```
**Frontend LLM Prompt Hint:** "Generate a user registration form with username and password fields. On submission, send a POST request to `/api/v1/users/` with the form data. Display the returned user ID and username upon successful creation."

---

## 2. Chat Session Endpoints

**Purpose:** To initiate, manage, and interact with AI chat sessions.

### `POST /sessions/`
**Description:** Starts a new chat session for a user with an initial message.
**Request Body (JSON):**
```json
{
  "user_id": 0,
  "initial_message": "string"
}
```
**Response (JSON):**
```json
{
  "id": "string",
  "user_id": 0,
  "title": "string",
  "created_at": "2025-09-29T12:00:00.000Z",
  "updated_at": "2025-09-29T12:00:00.000Z",
  "messages": [
    {
      "id": "string",
      "session_id": "string",
      "sender_type": "user" | "ai",
      "content": "string",
      "tool_names_used": ["string"],
      "timestamp": "2025-09-29T12:00:00.000Z"
    }
  ]
}
```
**Frontend LLM Prompt Hint:** "Create a 'Start New Chat' button. When clicked, prompt the user for their user ID and an initial message. Send this data as a POST request to `/api/v1/sessions/`. Display the returned chat session details, including the initial AI response, in a chat interface."

### `POST /sessions/chat`
**Description:** Sends a new message to an existing chat session and receives an AI response.
**Request Body (JSON):**
```json
{
  "session_id": "string",
  "user_id": 0,
  "content": "string"
}
```
**Response (JSON):**
```json
{
  "session_id": "string",
  "user_message": {
    "id": "string",
    "session_id": "string",
    "sender_type": "user",
    "content": "string",
    "tool_names_used": [],
    "timestamp": "2025-09-29T12:00:00.000Z"
  },
  "ai_response": {
    "id": "string",
    "session_id": "string",
    "sender_type": "ai",
    "content": "string",
    "tool_names_used": ["string"],
    "timestamp": "2025-09-29T12:00:00.000Z"
  },
  "tool_names_used": ["string"]
}
```
**Frontend LLM Prompt Hint:** "In an active chat session (given `session_id` and `user_id`), create an input field for the user to type messages. On sending a message, make a POST request to `/api/v1/sessions/chat` with the message content. Append both the user's message and the AI's response to the chat history display."

### `GET /sessions/{session_id}`
**Description:** Retrieves a specific chat session and all its messages.
**Path Parameters:**
*   `session_id` (string): The ID of the chat session.
**Response (JSON):**
```json
{
  "id": "string",
  "user_id": 0,
  "title": "string",
  "created_at": "2025-09-29T12:00:00.000Z",
  "updated_at": "2025-09-29T12:00:00.000Z",
  "messages": [
    {
      "id": "string",
      "session_id": "string",
      "sender_type": "user" | "ai",
      "content": "string",
      "tool_names_used": ["string"],
      "timestamp": "2025-09-29T12:00:00.000Z"
    }
  ]
}
```
**Frontend LLM Prompt Hint:** "When a user selects an existing chat session from a list (identified by `session_id`), fetch its complete history by making a GET request to `/api/v1/sessions/{session_id}`. Populate the chat interface with all messages from the response."

### `GET /sessions/user/{user_id}`
**Description:** Lists all chat sessions for a specific user.
**Path Parameters:**
*   `user_id` (integer): The ID of the user.
**Response (JSON):**
```json
{
  "sessions": [
    {
      "id": "string",
      "user_id": 0,
      "title": "string",
      "created_at": "2025-09-29T12:00:00.000Z",
      "updated_at": "2025-09-29T12:00:00.000Z",
      "messages": []
    }
  ]
}
```
**Frontend LLM Prompt Hint:** "Create a sidebar or a 'My Chats' section. Given a `user_id`, make a GET request to `/api/v1/sessions/user/{user_id}` to retrieve a list of all chat sessions. Display these sessions as clickable items, showing their title and creation date."

---

## Data Models (for reference)

### `UserCreate`
```python
class UserCreate(BaseModel):
    username: str
    password: str
```

### `UserSchema`
```python
class UserSchema(BaseModel):
    id: int
    username: str
```

### `SessionCreate`
```python
class SessionCreate(BaseModel):
    user_id: int
    initial_message: str
```

### `MessageRequest`
```python
class MessageRequest(BaseModel):
    session_id: str
    user_id: int
    content: str
```

### `ChatMessageResponse`
```python
class ChatMessageResponse(BaseModel):
    id: str
    session_id: str
    sender_type: Literal["user", "ai"]
    content: str
    tool_names_used: List[str] = []
    timestamp: datetime
```

### `ChatSessionResponse`
```python
class ChatSessionResponse(BaseModel):
    id: str
    user_id: int
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[ChatMessageResponse]
```

### `MessageResponse`
```python
class MessageResponse(BaseModel):
    session_id: str
    user_message: ChatMessageResponse
    ai_response: ChatMessageResponse
    tool_names_used: List[str]
```

### `SessionListResponse`
```python
class SessionListResponse(BaseModel):
    sessions: List[ChatSessionResponse]
```

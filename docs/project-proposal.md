# Distributed To-Do List Manager Project Proposal

Develop a to-do list manager where tasks are synchronized across multiple clients. The project must handle concurrent access and resolve conflicts when tasks are modified offline. This involves software design for distributed systems, network programming, and conflict resolution algorithms.

## Key Features

* **Client/Server architecture:** A server handles data synchronization. Clients operate locally, but can synchronize with the server. The client can be configured to point at a different server.
* **Configuration:** The client can be configured via YAML with a username and sync server. Task lists on a server are associated with a username.
* **Task management:** Users can create, modify, view, and delete tasks. A task has a description, a system-generated GUID, a completed status, a creation date, a modified date, a creator, a last editor, and an optional due date.
* **Offline operation:** All tasks are cached locally, and all operations happen locally first. The client retains a log of operations performed.
* **Task synchronization:** Updates are synced remotely on an ad-hoc basis; a command “sync” must be run to sync, as there is no daemon running to sync changes in the background. The server retains a record of operations synced from a client. On a client sync request, the server will reconcile the client’s state and the server’s state, comparing the client’s log of operations and the server’s.
* **Task update conflict resolution:** When syncing, if a task has been modified locally as well as remotely, the server will accept whichever change is more recent. The client will give the user a message explaining this.
* **Completing tasks:** A task can be marked as completed. The client and server will retain up to 10 completed tasks. Once an 11th task is completed, the oldest completed task is deleted.
* **Comprehensive help:** The client can present a user with documentation on how to use each command, as well as a summarized guide of the commands available and the general flow of usage.


# Initial Design and Structure

* **Project:** Distributed To-Do List Manager

* **Repository:** https://github.com/BenOvermyer/distributed-todo

## General Architecture

### Overview

This system is meant to allow users to manage tasks (“to dos”) in a distributed fashion. It has a command-line environment and operates as independent client and server programs. Packaging and distribution are outside the scope of this project.

### System Components

The following are the components that make up the full system:

* Client program 
* Client database
* Client configuration
* Server program
* Server database
* Server configuration

### Communication Model

The client and server communicate with each other via HTTP. The server is structured as a RESTful API, which the client calls when syncing data.

### Data Flow

Most usage of the client does not require or use the server. The only time the client ever communicates with the server is when the user triggers a synchronization operation. When this happens, the client sends its state and its operation log to the server. The server will respond with an HTTP response of 200 and a JSON body including a list of operations for the client to apply locally to match the reconciled server state. If something goes wrong, the server will respond with an HTTP response of 4xx or 5xx with a JSON body including an error message, and the client will output the error to the user.

### Persistence and Storage

Both the server and client maintain SQLite databases locally in order to manage state. Neither program communicates directly with the database of another program. All data operations are managed by the program that “owns” the database.

SQLite is chosen for its relational nature and ease of use.

## Security Considerations

Users will have a username associated with their tasks. This username is configured locally with the client. There is no authentication or authorization in place. This is an intentional design choice to allow for rapid development and to recollect the early days of IRC. The design accepts that malicious users could do nefarious things in the name of a different user. That’s part of the fun. Similarly, all network traffic will be transmitted in clear text.

The application will, however, do input validation to ensure that the data does not get into a state that cannot be recovered. Also, all operations will be logged, including identifying information for clients.

## Client Program Structure

### Overview

The client program is the workhorse of the system. The user will interact with the client to create, view, update, and delete tasks. The user can also sync with a remote server using the client.

### Command Structure

The client will support the following commands:

* **list:** show all tasks. By default, it doesn’t show completed tasks.
* **complete:** completes the task with the specified ID
* **create:** creates a new task with the specified text.
* **init:** creates a config file .todo with sane defaults in the directory of the program’s main script
* **delete:** deletes the specified task, with confirmation.
* **update:** updates the specified task with the new text given
* **due:** updates the specified task to have the specified due date
* **sync:** synchronizes local state with a remote server
* **undue:** removes the due date from the specified task

Any command that refers to a “specified task” takes a positional argument with a numeric ID.

Appending the argument `--help` to any command will ignore the normal operation of that command and instead present documentation for the usage of that command.

The list command has the most arguments. The bare command just lists all active tasks. It also accepts a `--completed` argument that will show only completed tasks, or a `--today` argument that only shows tasks due today. Passing both arguments will show all tasks that have been completed today.

All commands will avoid interactive prompts when possible. Even the delete command, which has an interactive prompt to confirm deletion by default, will have an optional `--force` argument that will automatically confirm deletion. The point of this is to make the client as composable as possible.

The sync command will also accept the `--force` argument. In this case, any conflicts encountered will be overwritten with the client’s version of the operational log.

### Configuration

The client uses a configuration file in a basic ini-style format. It checks for a config file `.todo` first in the directory of the program’s main script, then in the user’s home directory. If it doesn’t find the file in either location, then it reports an error to the user and exits.

The configuration file looks like this:

```ini
server_url=http://localhost:9777
username=bob
database_file=todo.db
```

### Data Retention

The client will retain the last 10 completed tasks. When an 11th is completed, the task with the oldest completion date will be deleted. The operation log, on the other hand, will retain the last 200 actions taken.

## Data Structures

The primary elements in play are a Task and an Operational Log Entry. These will be represented as dictionaries in Python. The structure given in tables is their SQLite representation.

### Task Data Structure

| Field | Type |
| ----- | ---- |
| id | integer |
| username | text |
| content | text |
| is_completed | integer |
| due_date | text |
| created_at | text |
| updated_at | text |

### Log Entry Data Structure

| Field | Type |
| ----- | ---- |
| username | text |
| log_date | text |
| task_id | integer |
| operation | text |
| operation_content | text |

## Server Program Structure

### Overview

The primary purpose of the server is to synchronize data between clients. It presents a RESTful API for this.

### Style and Dependencies

The program is structured in a loose functional style in order to make testing easier. We will not use test-driven development, but we will use unit tests to ensure correctness.

It will use FastAPI for the API framework to accelerate development.

## Synchronization Model

Every time the client does an operation that would change its data, an entry is put into the client’s operational log in the database. This entry includes the timestamp, the id of the task, the type of operation (create, change due date, change completion, change text, or delete), and the content of the operation (e.g., the new due date).

When a client issues a synchronization request to a server, it also sends its operational log to the server as part of the payload. The server checks its own operational log for the username associated with the client. The matching log entries are made into a new tuple in order of timestamp. Then, the server compares this tuple to the client’s incoming operational log. If they match, the server immediately returns a 204 response. If they do not match, then the server begins a sync operation.

If the client has entries that the server doesn’t, then the server replays those entries’ operations against its own data and then returns a 204 response. If the server has entries that the client doesn’t, the server returns a 200 response, along with a payload of the entries that the client is missing. If both are missing different entries, the server replays the client’s operations against its database, then returns a 200 response along with the entries the client is missing.

When a sync operation occurs, any operations logs are entered into the client or server’s operations logs exactly as they were originally. This includes the timestamp.

When carrying out delete operations, if the relevant task doesn’t exist in the database (for either client or server), the deletion is not carried out, but the operation log is entered into the system.

### Conflict Resolution

If an operation would conflict with the existing state of the database, then the system will do its best to ensure a stable state. If the user used the --force flag for a sync operation, then whatever is in the client’s operation log will be used to overwrite the server’s state in the event of conflicts. Otherwise, the following procedure applies.

In the event that a creation task is attempted from the operation log and a task with that id already exists, then the program applying the operation will compare the text of the task in the database to the text of the create operation. If they are identical, then the operation is skipped as successful. If they differ, then the program marks the operation as failed, and any further operations logs that refer to that task id are skipped. Once the sync operation completes, if the failed operation happened on the server, the server sends a 409 response, with all of the failed operations and skipped operations in the payload. The client will then display an error message and a list of failed and skipped operations.

If the `--force` argument was used and conflicts were addressed this way, then the server will include a list of operations that conflicted but were force-applied in the response payload to the client.

## Error Handling

Most errors will be transactional. In these cases, the server will send a message to the client along with an appropriate HTTP status code in response to the request that triggered the error. In this case, the client should display the error message to the user.

If the server encounters an error that it cannot recover from, it should terminate and allow outside processes to handle restarting it. The client should display a message to the user in such cases saying that the server cannot be reached.

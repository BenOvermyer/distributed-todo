#!/usr/bin/env bash

echo "Demonstration script running..."

docker compose down -v
docker compose up -d

cd todo-client

rm -f ~/.todo_client/config.ini ~/.todo_client/config2.ini
rm -f todo_client.db todo_client2.db
uv run todo-client init
sed -i 's/default_user/demo/g' ~/.todo_client/config.ini
cp ~/.todo_client/config.ini ~/.todo_client/config2.ini
sed -i 's/todo_client.db/todo_client2.db/g' ~/.todo_client/config2.ini

client() {
    local config="$1"
    shift
    local cmd="uv run todo-client --config $config $*"
    echo -e "\$ \033[0;34m$cmd\033[0m"
    uv run todo-client --config "$config" "$@"
}
client1() {
    client ~/.todo_client/config.ini "$@"
}
client2() {
    client ~/.todo_client/config2.ini "$@"
}
pause_for_effect() {
    echo -e "\nPress any key to continue...\n"
    read -n 1 -s
}
announce() {
    echo -e "\n\033[0;32m$1\033[0m\n"
}

announce "Initialization done"

pause_for_effect

announce "The help output for the client"

client1 -h

pause_for_effect

announce "Client 1 task list"

client1 list

announce "Client 2 task list"

client2 list

pause_for_effect

announce "Creating a task on client 1"

client1 create "Demo Task from Client 1"

pause_for_effect

announce "Client 1 task list after creating a task"

client1 list

pause_for_effect

announce "Client 2 task list after client 1 created a task"

client2 list

pause_for_effect

announce "Adding a few more tasks for client 1"

client1 create "Second Task from Client 1"
client1 create "Third Task from Client 1"

pause_for_effect

announce "Making a task have a due date"

client1 due 1 "2025-12-01"

client1 list

pause_for_effect

announce "Completing a task"

client1 complete 2

client1 list

pause_for_effect

announce "Synchronizing from client 1"

client1 sync

pause_for_effect

announce "Synchronizing from client 2"

client2 sync

pause_for_effect

announce "Client 2 task list after synchronization"

client2 list

pause_for_effect

announce "Showing tasks completed today, from client 2"

client2 list --completed --today

pause_for_effect

announce "Add another task for client 1, then update a task with client 2"

client1 create "Fourth Task from Client 1"

client2 update 3 "Updated Third Task from Client 2"

pause_for_effect

announce "Synchronizing both clients - client 1 twice to show idempotency"

client1 sync

client2 sync

client1 sync

client1 list

client2 list

pause_for_effect
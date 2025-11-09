from prettytable import PrettyTable


def get_task_table(tasks):
    """
    Return an ASCII table representation of the given list of Task objects.

    I'm using PrettyTable here because I don't want to implement table formatting myself for this POC.
    """

    table = PrettyTable()
    table.field_names = [
        "ID",
        "Content",
        "Completed",
        "Due Date",
        "Created At",
        "Updated At",
    ]

    for task in tasks:
        table.add_row(
            [
                task.id,
                task.content,
                "✅" if task.is_completed else "❌",
                task.due_date if task.due_date else "-",
                task.created_at,
                task.updated_at,
            ]
        )

    return table

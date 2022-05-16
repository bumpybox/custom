import sys
import traceback

import ftrack_api


def main(project, asset, task, status_name):
    session = ftrack_api.Session()

    if task:
        task = session.query(
            "Task where project.full_name is \"{0}\" and name is "
            "\"{1}\" and parent.name is "
            "\"{2}\"".format(project, task, asset)
        ).one()
    else:
        task = session.query(
            "TypedContext where project.full_name is \"{0}\" and name"
            " is \"{1}\"".format(project, asset)
        ).one()

    task["status"] = session.query(
        "Status where name is \"{}\"".format(status_name)
    ).one()

    hierarchy = []
    for item in task['link']:
        hierarchy.append(session.get(item['type'], item['id']))

    hierarchy_path = "/".join([x["name"] for x in hierarchy])

    print("Setting \"{}\" to \"{}\".".format(hierarchy_path, status_name))

    session.commit()


if __name__ == "__main__":
    try:
        main(sys.argv[-4], sys.argv[-3], sys.argv[-2], sys.argv[-1])
    except Exception:
        print(traceback.format_exc())
        raise ValueError(traceback.format_exc())

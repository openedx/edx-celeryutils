"""
Parallelize a large task and join the results, using a database backend without a busy wait
"""


def chunk_task(task, std_args, itr_arg_name, itr_arg, chunk_size, callback, callback_args):
    """
    Start a bunch of subtasks with a joined callback to follow.

        task: the task to run as subtasks
        std_args: task arguments that do not change
        itr_arg_name: the name of the argument to be chunked
        itr_arg: the (unchunked) argument to be chunked, a list
        chunk_size: the number of items to put in each chunk
        callback: the task to run after all subtasks have finished
        callback_args: callback arguments that do not depend on the results of subtasks
    """
    parent = TaskCounter()
    parent.save()  # if we knew the total length of itr_arg here, we could set parent.expected before saving and remove all the "lock" nonsense

    def maybe_callback():
        if TaskCounter.is_finished(parent.id):
            callback_sig = callback.s(callback_args)
            callback_sig.apply_async(
                TaskCounter.results_itr(parent.id),
                link=TaskCounter.cleanup_after_callback
            )

    exhausted = False
    while not exhausted:
        itr_arg_list = []
        for _ in range(chunk_size):
            try:
                itr_arg_list.append(itr_arg.next())
            except StopIteration:
                exhausted = True
        parent.expected = parent.expected + 1
        subtask = task.s(**std_args.update({itr_arg_name: itr_arg_list}))
        t = subtask.freeze()

        def update_and_maybe_callback():
            TaskCounter.update(parent.id, t)
            maybe_callback()

        t.apply_async(link=update_and_maybe_callback)

    parent.locked = False
    parent.save()
    maybe_callback()

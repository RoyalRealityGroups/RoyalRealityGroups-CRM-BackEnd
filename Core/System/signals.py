from django.dispatch import Signal

# from TaskManagement.services import task_signal_handler

approval_event = Signal()
assignee_added_event = Signal()
multi_approved_event = Signal()

# task_approval_event = Signal()


# approval_event.connect(task_signal_handler, weak=False)


# from django.dispatch import receiver

# Define handler for approval event
# @receiver(approval_event)
# def handle_approval_event(sender, instance, approved_by, **kwargs):
#     print(f"Approval event triggered for {instance} by {approved_by}")

# # Define handler for assignee added event
# @receiver(assignee_added_event)
# def handle_assignee_added_event(sender, instance, assignee, **kwargs):
#     print(f"Assignee {assignee} added to {instance}")

#---------------Example Usage---------------
# def approve_task(task):
#     task.is_approved = True
#     task.save()

#     # Dynamically trigger approval event
#     approval_event.send(sender=task.__class__, instance=task, event_name="approval")



# def assign_user_to_task(task, user):
#     task.assignees.add(user)

#     # Dynamically trigger assignee added event
#     assignee_added_event.send(sender=task.__class__, instance=task, event_name="assignee_added")

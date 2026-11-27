from apps.jobs.models import SavedJob


class SavedJobService:
    @staticmethod
    def toggle(user, job) -> bool:
        """Save or un-save. Returns ``True`` when the job is now saved."""
        obj, created = SavedJob.objects.get_or_create(user=user, job=job)
        if not created:
            obj.delete()
        return created

    @staticmethod
    def saved_ids(user) -> set:
        if not user.is_authenticated:
            return set()
        return set(SavedJob.objects.filter(user=user).values_list("job_id", flat=True))

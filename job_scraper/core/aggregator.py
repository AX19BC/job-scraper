from models import Job


def aggregate(job_lists: list[list[Job]]) -> list[Job]:
    seen: dict[str, Job] = {}
    for jobs in job_lists:
        for job in jobs:
            if job.url in seen:
                existing = seen[job.url]
                if job.portal not in existing.portal:
                    existing.portal = f"{existing.portal}, {job.portal}"
            else:
                seen[job.url] = job
    return list(seen.values())

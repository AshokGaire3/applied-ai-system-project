# PawPal+ — Class diagram (for `uml_diagram.png`)

This diagram reflects **`pawpal_system.py`** (`Task`, `Pet`, `Owner`, `Scheduler`).

**Export for submission:** Copy only the fenced block below into **[Mermaid Live Editor](https://mermaid.live/)** -> Actions -> **Export PNG** -> save as `assets/uml_diagram.png`.

```mermaid
classDiagram
    class Task {
        +str description
        +int duration_minutes
        +str priority
        +str frequency
        +Optional~str~ start_time
        +bool completed
        +Optional~date~ last_completed_date
        +Optional~date~ next_due_date
        +mark_complete(on_date) None
        +reset() None
        +is_due(on_date) bool
        +priority_rank() int
        +end_time() Optional~str~
        +to_dict() dict
        +from_dict(data)$ Task
    }

    class Pet {
        +str name
        +str species
        +float age_years
        -list _tasks
        +add_task(task) None
        +remove_task(description) bool
        +get_tasks() list
        +get_due_tasks(on_date) list
        +reset_daily_tasks() None
        +total_task_time() int
        +to_dict() dict
        +from_dict(data)$ Pet
    }

    class Owner {
        +str name
        +int available_minutes_per_day
        -list _pets
        +add_pet(pet) None
        +remove_pet(name) bool
        +get_pets() list
        +get_all_tasks() list
        +get_all_due_tasks(on_date) list
        +total_due_minutes(on_date) int
        +save_to_json(filepath) None
        +load_from_json(filepath)$ Owner
    }

    class Scheduler {
        +Owner owner
        +build_daily_plan(on_date) list
        +sort_by_time(tasks) list
        +filter_tasks(pet_name, completed) list
        +detect_conflicts(plan) list
        +detect_time_conflicts(pairs) list
        +get_unscheduled_tasks(plan, on_date) list
        +advance_day() None
        +summary(plan) str
        -_explain(pet, task, elapsed) str
        -_min_to_time(minutes) str
        -_hhmm_to_min(hhmm) int
    }

    Owner "1" *-- "0..*" Pet : owns
    Pet "1" *-- "0..*" Task : has
    Scheduler "1" --> "1" Owner : schedules for
    Scheduler ..> Pet : reads via Owner
    Scheduler ..> Task : reads via Pet
```

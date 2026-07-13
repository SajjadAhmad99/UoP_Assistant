# if __name__ == "__main__":

#     # Paste your full HTML here (the <article>...</article> content)
#     INDEX_HTML = """<your pasted HTML here>"""   # ← replace with the provided HTML

#     departments = parse_departments_from_html(INDEX_HTML)
#     print(f"Found {len(departments)} departments.")

#     # Optional: limit for testing
#     # departments = departments[:8]

#     tasks = [create_scrape_task(dept) for dept in departments]

#     # Create crew – process sequentially or in batches (CrewAI parallel support is limited, so we batch)
#     BATCH_SIZE = 10
#     all_results = []

#     for i in range(0, len(tasks), BATCH_SIZE):
#         batch_tasks = tasks[i:i + BATCH_SIZE]
#         print(f"Processing batch {i//BATCH_SIZE + 1} ({len(batch_tasks)} tasks)...")

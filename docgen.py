#!/bin/python3

def import_from_path(module_name, file_path):
    import importlib.util

    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

FILES = [
    "routes/api/routes_posts.py"
    # "routes/api/routes_progress.py"
    # "routes/api/routes_search.py"
    # "routes/api/routes_users.py"
]
def treegen_repo():
    tree = {
        "endpoints": []
    }

    for file in FILES:
        mod = import_from_path(f"DOCGEN_{file}", file)
        eps = mod.all_endpoints()
        for ep in eps:
            tree["endpoints"].append(ep._to_dict(ep))

    return tree

def docgen_repo():
    tree = treegen_repo()
    
    import yaml
    return yaml.dump(tree, None)

if __name__ == "__main__":
    print(docgen_repo())

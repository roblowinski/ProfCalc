# =============================================================================
# Import Graph Analysis Script
# =============================================================================
#
# FILE: scripts/analysis/import_graph.py
#
# PURPOSE:
# This script analyzes the import relationships within the profcalc package,
# building a directed graph of module dependencies and identifying strongly
# connected components. It helps detect circular import issues and understand
# the package's dependency structure.
#
# WHAT IT'S FOR:
# - Analyzing intra-package import relationships
# - Detecting circular import dependencies (cycles)
# - Understanding module coupling and dependencies
# - Supporting refactoring and architecture decisions
# - Providing insights into package structure
#
# WORKFLOW POSITION:
# This script is used during development and maintenance to analyze the
# package's internal structure. It helps identify potential architectural
# issues and supports decisions about module organization and dependencies.
#
# LIMITATIONS:
# - Only analyzes static imports within profcalc package
# - Cannot detect runtime or conditional imports
# - Limited to explicit import statements
# - Does not analyze external package dependencies
#
# ASSUMPTIONS:
# - All relevant modules are under src/profcalc
# - Import statements follow standard Python conventions
# - Module structure reflects package organization
# - Files are syntactically correct Python
#
# =============================================================================

"""Static import graph scanner for profcalc package.

Parses Python files under src/profcalc, extracts intra-package imports (e.g., from profcalc.common import ... or from .common import ...),
builds a directed graph and finds strongly connected components (SCCs). SCCs of size>1 indicate potential cycles.
"""
import ast
import os
import sys
from collections import defaultdict

ROOT = os.path.join(os.getcwd(), 'src', 'profcalc')

modules = {}  # module_name -> file_path
for dirpath, dirnames, filenames in os.walk(ROOT):
    for fn in filenames:
        if not fn.endswith('.py'):
            continue
        fp = os.path.join(dirpath, fn)
        rel = os.path.relpath(fp, ROOT)
        mod = 'profcalc.' + rel[:-3].replace(os.sep, '.')
        if mod.endswith('.__init__'):
            mod = mod[: -len('.__init__')]
        modules[mod] = fp

print(f'Found {len(modules)} python modules in profcalc')

# parse imports
graph = defaultdict(set)  # module -> set(imported module)

for mod, fp in modules.items():
    try:
        with open(fp, 'r', encoding='utf-8') as f:
            src = f.read()
    except Exception as e:
        print(f'Failed to read {fp}: {e}')
        continue
    try:
        tree = ast.parse(src, filename=fp)
    except SyntaxError as e:
        print(f'Syntax error parsing {fp}: {e}')
        continue

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                name = n.name
                if name.startswith('profcalc'):
                    graph[mod].add(name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module
            level = node.level
            if module is None:
                # relative import like "from . import X"
                # resolve based on level
                base_parts = mod.split('.')
                if level > 0:
                    base = base_parts[: -level]
                else:
                    base = base_parts
                if base:
                    graph[mod].add('.'.join(base))
            else:
                # handle relative like from .common import X -> module startswith profcalc
                if module.startswith('profcalc'):
                    graph[mod].add(module)
                elif module.startswith('.'):
                    # rare; module is relative
                    # normalize by counting leading dots
                    dots = 0
                    for ch in module:
                        if ch == '.':
                            dots += 1
                        else:
                            break
                    rel = module[dots:]
                    base_parts = mod.split('.')
                    if level > 0:
                        base = base_parts[: -level]
                    else:
                        base = base_parts
                    if rel:
                        full = base + [rel]
                    else:
                        full = base
                    graph[mod].add('.'.join(full))
                else:
                    # relative import using level
                    if level > 0:
                        base_parts = mod.split('.')
                        base = base_parts[: -level]
                        if module:
                            full = base + [module]
                        else:
                            full = base
                        graph[mod].add('.'.join(full))

# Restrict graph nodes to modules we know
for m in list(graph):
    newset = set()
    for imp in graph[m]:
        # only track imports that are inside the profcalc package
        if imp in modules:
            newset.add(imp)
        else:
            # sometimes imports target submodules like profcalc.common.bmap_io
            # check prefix match
            for known in modules:
                if imp == known or imp.startswith(known + '.'):
                    newset.add(known)
                    break
    graph[m] = newset

# Find SCCs using Tarjan
index = 0
indices = {}
lowlink = {}
stack = []
onstack = set()
sccs = []

sys.setrecursionlimit(10000)

def strongconnect(v):
    global index
    indices[v] = index
    lowlink[v] = index
    index += 1
    stack.append(v)
    onstack.add(v)

    for w in graph.get(v, []):
        if w not in indices:
            strongconnect(w)
            lowlink[v] = min(lowlink[v], lowlink[w])
        elif w in onstack:
            lowlink[v] = min(lowlink[v], indices[w])

    if lowlink[v] == indices[v]:
        comp = []
        while True:
            w = stack.pop()
            onstack.remove(w)
            comp.append(w)
            if w == v:
                break
        sccs.append(comp)

for v in modules:
    if v not in indices:
        strongconnect(v)

# Report SCCs larger than 1
cycles = [c for c in sccs if len(c) > 1]

if not cycles:
    print('No import cycles detected among profcalc modules (static scan)')
else:
    print(f'Detected {len(cycles)} strongly-connected components (>1 module):')
    for comp in cycles:
        print('\nCycle:')
        for m in comp:
            print('  -', m)

if cycles:
    # Exit non-zero so CI can fail when cycles are detected
    sys.exit(2)

# Also report modules that import many others (hotspots)
hot = sorted(((m, len(graph[m])) for m in graph), key=lambda x: -x[1])[:10]
print('\nTop importers:')
for m, c in hot:
    print(f'  {m}: imports {c} internal modules')

# Optionally dump graph size
edges = sum(len(s) for s in graph.values())
print(f'\nGraph: {len(modules)} nodes, {edges} intra-package edges')

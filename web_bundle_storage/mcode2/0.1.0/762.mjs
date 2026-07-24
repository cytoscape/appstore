export const __webpack_esm_id__ = 762;
export const __webpack_esm_ids__ = [762];
export const __webpack_esm_modules__ = {

/***/ 9762
(__unused_webpack_module, __webpack_exports__, __webpack_require__) {


// EXPORTS
__webpack_require__.d(__webpack_exports__, {
  "default": () => (/* binding */ components_MCODEPanel)
});
// ESM COMPAT FLAG
__webpack_require__.r(__webpack_exports__);

// EXTERNAL MODULE: ./node_modules/react/jsx-runtime.js
var jsx_runtime = __webpack_require__(4848);
// EXTERNAL MODULE: ./node_modules/@mui/icons-material/Add.js
var Add = __webpack_require__(6718);
// EXTERNAL MODULE: ./node_modules/@mui/icons-material/Check.js
var Check = __webpack_require__(4017);
// EXTERNAL MODULE: ./node_modules/@mui/icons-material/Delete.js
var Delete = __webpack_require__(7034);
// EXTERNAL MODULE: ./node_modules/@mui/icons-material/ExpandLess.js
var ExpandLess = __webpack_require__(1656);
// EXTERNAL MODULE: ./node_modules/@mui/icons-material/FileDownload.js
var FileDownload = __webpack_require__(399);
// EXTERNAL MODULE: ./node_modules/@mui/icons-material/Info.js
var Info = __webpack_require__(5897);
// EXTERNAL MODULE: ./node_modules/@mui/icons-material/Menu.js
var Menu = __webpack_require__(2274);
// EXTERNAL MODULE: ./node_modules/@mui/icons-material/Palette.js
var Palette = __webpack_require__(6954);
// EXTERNAL MODULE: consume shared module (default) react@!=1.8...3...1 (singleton)
var consume_shared_module_default_react_1_8_3_singleton_ = __webpack_require__(7309);
// EXTERNAL MODULE: consume shared module (default) @mui/material@!=5...1.8...0 (singleton)
var material_5_1_8_singleton_ = __webpack_require__(7816);
// EXTERNAL MODULE: ./node_modules/cytoscape/dist/cytoscape.esm.mjs
var cytoscape_esm = __webpack_require__(165);
// EXTERNAL MODULE: ./node_modules/cytoscape-euler/cytoscape-euler.js
var cytoscape_euler = __webpack_require__(1203);
var cytoscape_euler_default = /*#__PURE__*/__webpack_require__.n(cytoscape_euler);
// EXTERNAL MODULE: remote cyweb/EventBus
var EventBus = __webpack_require__(9788);
// EXTERNAL MODULE: remote cyweb/ElementApi
var ElementApi = __webpack_require__(254);
// EXTERNAL MODULE: remote cyweb/SelectionApi
var SelectionApi = __webpack_require__(800);
// EXTERNAL MODULE: remote cyweb/TableApi
var TableApi = __webpack_require__(5322);
// EXTERNAL MODULE: remote cyweb/WorkspaceApi
var WorkspaceApi = __webpack_require__(2695);
;// ./src/model/mcodeExport.ts
/**
 * Score formatted with up to 3 fraction digits, trailing zeros stripped
 * (matches the Java NumberFormat with maximumFractionDigits = 3): e.g.
 * 2.3333 -> "2.333", 2 -> "2", 1.6 -> "1.6".
 */
function formatScore(score) {
    return String(Number(score.toFixed(3)));
}
/**
 * Build the MCODE results report text. The cluster rank is the row's 1-based
 * position in `rows` (which are expected to already be in ranked order).
 *
 * `now` is injectable so the output is deterministic in tests.
 */
function buildMcodeResultsText(parameters, rows, now = new Date()) {
    const p = parameters;
    const lines = [
        'MCODE App Results',
        `Date: ${now.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'medium' })}`,
        '',
        'Parameters:',
        '   Network Scoring:',
        `      Include Loops: ${p.includeLoops}  Degree Cutoff: ${p.degreeCutoff}`,
        '   Cluster Finding:',
        `      Node Score Cutoff: ${p.nodeScoreCutoff}  Haircut: ${p.haircut}  Fluff: ${p.fluff}` +
            `  K-Core: ${p.kCore}  Max. Depth from Seed: ${p.maxDepthFromStart}`,
        '',
        'Cluster\tScore (Density*#Nodes)\tNodes\tEdges\tNode IDs',
    ];
    rows.forEach((row, i) => {
        lines.push(`${i + 1}\t${formatScore(row.score)}\t${row.nodeCount}` +
            `\t${row.edgeCount}\t${row.nodeNames.join(', ')}`);
    });
    return lines.join('\n') + '\n';
}
/**
 * Slice a source network's CX2 stream down to a single cluster: keep only the
 * cluster's nodes (with coordinates overridden from `nodePositions` when
 * present, so the importer runs no layout) and the edges whose endpoints are
 * both in the cluster, and fix up the metaData element counts to match.
 *
 * Operates on the loosely-typed CX2 aspect array (`any[]`); the caller casts
 * the result to the cyweb `Cx2` type when handing it to createNetworkFromCx2.
 */
function sliceClusterCx2(cx2, clusterNodeIds, nodePositions) {
    const clusterNodes = new Set(clusterNodeIds);
    let nodeCount = 0;
    let edgeCount = 0;
    const sliced = cx2.map((aspect) => {
        if (Array.isArray(aspect.nodes)) {
            const nodes = aspect.nodes
                .filter((n) => clusterNodes.has(String(n.id)))
                .map((n) => {
                const pos = nodePositions?.[String(n.id)];
                return pos ? { ...n, x: pos.x, y: pos.y } : n;
            });
            nodeCount = nodes.length;
            return { nodes };
        }
        if (Array.isArray(aspect.edges)) {
            const edges = aspect.edges.filter((e) => clusterNodes.has(String(e.s)) && clusterNodes.has(String(e.t)));
            edgeCount = edges.length;
            return { edges };
        }
        return aspect;
    });
    for (const aspect of sliced) {
        if (Array.isArray(aspect.metaData)) {
            for (const meta of aspect.metaData) {
                if (meta.name === 'nodes' && meta.elementCount !== undefined)
                    meta.elementCount = nodeCount;
                if (meta.name === 'edges' && meta.elementCount !== undefined)
                    meta.elementCount = edgeCount;
            }
        }
    }
    return sliced;
}
// ── MCODE node-table columns ────────────────────────────────────────────────
/** Namespace prefixing every MCODE node-table column. */
const MCODE_NAMESPACE = 'MCODE';
/**
 * Column name for an MCODE node attribute and result number, e.g.
 * `mcodeColumnName('Score', 1)` -> "MCODE::Score (1)". Mirrors the Java
 * `MCODEUtil.columnName(name, result)`.
 */
function mcodeColumnName(attr, resultNumber) {
    return `${MCODE_NAMESPACE}::${attr} (${resultNumber})`;
}
/** The three node-table column names MCODE creates for a given result. */
function mcodeColumnNames(resultNumber) {
    return [
        mcodeColumnName('Score', resultNumber),
        mcodeColumnName('Node Status', resultNumber),
        mcodeColumnName('Clusters', resultNumber),
    ];
}
/**
 * Build the node-table columns and row values for an MCODE result, mirroring
 * `MCODEAnalyzeTask.createNetworkAttributes()`:
 *   - "MCODE::Score (n)"       (double)          : the node's MCODE score
 *   - "MCODE::Node Status (n)" (string)          : Unclustered | Clustered | Seed
 *   - "MCODE::Clusters (n)"    (list of string)  : e.g. ["Cluster 1", "Cluster 3"]
 *
 * Every scored node gets its score and defaults to "Unclustered"; nodes that
 * belong to clusters accumulate the cluster names and are marked "Seed" (when
 * the cluster's seed) or "Clustered". Nodes not analyzed simply keep the
 * column defaults.
 */
function buildMcodeNodeTableData(resultNumber, clusters, scores) {
    const scoreCol = mcodeColumnName('Score', resultNumber);
    const statusCol = mcodeColumnName('Node Status', resultNumber);
    const clustersCol = mcodeColumnName('Clusters', resultNumber);
    const columns = [
        { name: scoreCol, type: 'double', defaultValue: 0 },
        { name: statusCol, type: 'string', defaultValue: 'Unclustered' },
        { name: clustersCol, type: 'list_of_string', defaultValue: [] },
    ];
    const rows = {};
    // Every analyzed node gets its score and a default "Unclustered" status.
    for (const [nodeId, score] of Object.entries(scores)) {
        rows[nodeId] = { [scoreCol]: score, [statusCol]: 'Unclustered' };
    }
    // Nodes in clusters: accumulate cluster names (insertion order, de-duped) and
    // set the status. As in the Java version, when a node is in multiple clusters
    // the last one processed wins for the status value.
    for (const cluster of clusters) {
        const clusterName = `Cluster ${cluster.rank}`;
        for (const nodeId of cluster.nodes) {
            const row = rows[nodeId] ?? (rows[nodeId] = { [scoreCol]: scores[nodeId] ?? 0 });
            const list = row[clustersCol] ?? [];
            if (!list.includes(clusterName))
                list.push(clusterName);
            row[clustersCol] = list;
            row[statusCol] = cluster.seedId === nodeId ? 'Seed' : 'Clustered';
        }
    }
    return { columns, rows };
}

// EXTERNAL MODULE: remote cyweb/ExportApi
var ExportApi = __webpack_require__(4156);
// EXTERNAL MODULE: remote cyweb/NetworkApi
var NetworkApi = __webpack_require__(2148);
// EXTERNAL MODULE: remote cyweb/VisualStyleApi
var VisualStyleApi = __webpack_require__(8223);
;// ./src/model/useMcodeResultActions.ts
/**
 * Actions the user can run against a selected MCODE result / cluster from the
 * options menu: view the source network, apply the MCODE visual style, create a
 * cluster subnetwork, and export the result to a text file.
 *
 * These handlers are stateful (they consume Cytoscape Web API hooks), so they
 * live in a custom hook rather than a plain utility module. The pure data
 * transforms they rely on live in `mcodeExport.ts`.
 */







function useMcodeResultActions(selectedResult, selectedCluster) {
    const workspaceApi = (0,WorkspaceApi.useWorkspaceApi)();
    const networkApi = (0,NetworkApi.useNetworkApi)();
    const exportApi = (0,ExportApi.useExportApi)();
    const elementApi = (0,ElementApi.useElementApi)();
    const visualStyleApi = (0,VisualStyleApi.useVisualStyleApi)();
    const viewSourceNetwork = (0,consume_shared_module_default_react_1_8_3_singleton_.useCallback)(() => {
        if (!selectedResult)
            return;
        const res = workspaceApi.switchCurrentNetwork(selectedResult.networkId);
        if (!res.success) {
            console.warn('Failed to switch to source network:', res.error.message);
        }
    }, [selectedResult, workspaceApi]);
    const applyMcodeStyle = (0,consume_shared_module_default_react_1_8_3_singleton_.useCallback)(() => {
        if (!selectedResult)
            return;
        const { networkId, id, algorithm } = selectedResult;
        const statusColumn = mcodeColumnName('Node Status', id);
        const scoreColumn = mcodeColumnName('Score', id);
        const scores = Object.values(algorithm.getScores());
        const maxScore = scores.length > 0 ? Math.max(...scores) : 0;
        const warnOnFail = (label, result) => {
            if (!result.success)
                console.warn(`MCODE style: failed to ${label}:`, result.error.message);
        };
        // Default node size (remove any previous mapping).
        warnOnFail('remove node size width mapping', visualStyleApi.removeMapping(networkId, 'nodeWidth'));
        warnOnFail('remove node size height mapping', visualStyleApi.removeMapping(networkId, 'nodeHeight'));
        warnOnFail('set default node width', visualStyleApi.setDefault(networkId, 'nodeWidth', 40));
        warnOnFail('set default node height', visualStyleApi.setDefault(networkId, 'nodeHeight', 40));
        // Default node color.
        warnOnFail('set default node color', visualStyleApi.setDefault(networkId, 'nodeBackgroundColor', '#ffffff'));
        // Node shape mapped from the node-status column ("Seed" / "Clustered" / "Unclustered").
        /**     warnOnFail(
              'map node shape',
              visualStyleApi.createDiscreteMapping(
                networkId,
                'nodeShape',
                statusColumn,
                'string',
                { Seed: 'rectangle', Clustered: 'ellipse', Unclustered: 'diamond' },
              ),
            )
        
            // Node fill color mapped continuously from the node-score column: 0 (or below)
            // is white, fading from black up to red at the cluster's max score.
            warnOnFail(
              'map node color',
              visualStyleApi.createContinuousMapping(
                networkId,
                'nodeBackgroundColor',
                'color',
                scoreColumn,
                [0, maxScore],
                'double',
                [
                  { value: 0, vpValue: '#000000', inclusive: true },
                  { value: maxScore, vpValue: '#ff0000' },
                ],
                '#ffffff',
                '#ff0000',
              ),
            )*/
    }, [selectedResult, visualStyleApi]);
    const createClusterNetwork = (0,consume_shared_module_default_react_1_8_3_singleton_.useCallback)(() => {
        if (!selectedResult || !selectedCluster)
            return;
        // Export the source network to CX2 and slice it down to the cluster, rather
        // than building an edge list: CX2 carries the original node/edge table
        // attributes (and visual styles), so the subnetwork preserves them.
        const clusterName = `${selectedResult.name} (Cluster ${selectedCluster.rank})`;
        const exported = exportApi.exportToCx2(selectedResult.networkId, { networkName: clusterName });
        if (!exported.success) {
            console.warn('Failed to export source network:', exported.error.message);
            return;
        }
        const cxData = sliceClusterCx2(exported.data, selectedCluster.nodes, selectedCluster.nodePositions);
        const created = networkApi.createNetworkFromCx2({
            cxData: cxData,
            addToWorkspace: true,
            navigate: true,
        });
        if (!created.success) {
            console.warn('Failed to create cluster network:', created.error.message);
        }
    }, [selectedResult, selectedCluster, exportApi, networkApi]);
    const exportResult = (0,consume_shared_module_default_react_1_8_3_singleton_.useCallback)(() => {
        if (!selectedResult)
            return;
        const { networkId, algorithm, clusters, name } = selectedResult;
        const parameters = algorithm.getParameters();
        // Resolve a node's display name from the source network ("name" column),
        // falling back to the raw node id when no name attribute is present.
        const nodeName = (nodeId) => {
            const node = elementApi.getNode(networkId, nodeId);
            if (node.success) {
                const value = node.data.attributes.name ?? node.data.attributes['shared name'];
                if (value !== undefined && value !== null)
                    return String(value);
            }
            return nodeId;
        };
        // Count the edges induced by the cluster's nodes in the source network
        // (undirected, each unordered pair once) — i.e. the cluster's edge count.
        const inducedEdgeCount = (nodes) => {
            const inCluster = new Set(nodes);
            const seen = new Set();
            for (const nodeId of nodes) {
                const connected = elementApi.getConnectedNodes(networkId, nodeId);
                if (!connected.success)
                    continue;
                for (const neighbor of connected.data.nodeIds) {
                    if (!inCluster.has(neighbor))
                        continue;
                    seen.add(nodeId < neighbor ? `${nodeId}|${neighbor}` : `${neighbor}|${nodeId}`);
                }
            }
            return seen.size;
        };
        const rows = clusters.map((cluster) => ({
            score: cluster.score,
            nodeCount: cluster.nodes.length,
            edgeCount: inducedEdgeCount(cluster.nodes),
            nodeNames: cluster.nodes.map(nodeName),
        }));
        const content = buildMcodeResultsText(parameters, rows);
        // Name the file after the source network, e.g. "galFiltered-mcode-results.txt".
        const summary = workspaceApi.getNetworkSummary(networkId);
        const networkName = summary.success ? summary.data.name : name;
        const fileName = `${networkName}-mcode-results.txt`;
        // Trigger a browser download of the text file.
        const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const anchor = document.createElement('a');
        anchor.href = url;
        anchor.download = fileName;
        document.body.appendChild(anchor);
        anchor.click();
        anchor.remove();
        URL.revokeObjectURL(url);
    }, [selectedResult, elementApi, workspaceApi]);
    return { viewSourceNetwork, applyMcodeStyle, createClusterNetwork, exportResult };
}

;// ./src/model/mcodeGraph.ts
class MCODEGraph {
    /** Node ids contained in this graph. */
    nodes;
    nodeSet;
    /** Adjacency restricted to `nodeSet`; values are de-duplicated. */
    adjacency;
    /**
     * Build an induced subgraph over `nodeIds` using the supplied adjacency.
     * Any neighbor not in `nodeIds` is dropped, so the result is self-contained.
     */
    constructor(nodeIds, sourceAdjacency) {
        this.nodeSet = new Set(nodeIds);
        this.nodes = [...this.nodeSet];
        this.adjacency = new Map();
        for (const node of this.nodes) {
            const neighbors = sourceAdjacency.get(node) ?? [];
            const seen = new Set();
            const kept = [];
            for (const neighbor of neighbors) {
                // Keep only edges whose endpoint is inside this subgraph and
                // collapse parallel edges to a single entry.
                if (this.nodeSet.has(neighbor) && !seen.has(neighbor)) {
                    seen.add(neighbor);
                    kept.push(neighbor);
                }
            }
            this.adjacency.set(node, kept);
        }
    }
    get nodeCount() {
        return this.nodes.length;
    }
    /** Neighbors of `nodeId` within this graph (empty if absent). */
    neighbors(nodeId) {
        return this.adjacency.get(nodeId) ?? [];
    }
    /**
     * Degree of `nodeId` = number of merged undirected edges touching it.
     * A self-loop contributes 1 only when `includeLoops` is true.
     */
    degree(nodeId, includeLoops) {
        const neighbors = this.adjacency.get(nodeId);
        if (neighbors === undefined)
            return 0;
        let degree = 0;
        for (const neighbor of neighbors) {
            if (neighbor === nodeId) {
                if (includeLoops)
                    degree += 1;
            }
            else {
                degree += 1;
            }
        }
        return degree;
    }
    /**
     * Count of unique undirected edges in the graph. Each unordered pair is
     * counted once; self-loops are included only when `includeLoops` is true.
     */
    edgeCount(includeLoops) {
        const pairs = new Set();
        for (const node of this.nodes) {
            for (const neighbor of this.adjacency.get(node) ?? []) {
                if (neighbor === node) {
                    if (includeLoops)
                        pairs.add(`${node}|${node}`);
                    continue;
                }
                const pair = node < neighbor ? `${node}|${neighbor}` : `${neighbor}|${node}`;
                pairs.add(pair);
            }
        }
        return pairs.size;
    }
    /**
     * Graph density = actualEdges / possibleEdges.
     *
     *   possibleEdges = includeLoops ? n*(n+1)/2 : n*(n-1)/2
     *
     * Returns 0 when there are too few nodes to form any edge.
     */
    density(includeLoops) {
        const n = this.nodeCount;
        const possible = includeLoops ? (n * (n + 1)) / 2 : (n * (n - 1)) / 2;
        if (possible <= 0)
            return 0;
        return this.edgeCount(includeLoops) / possible;
    }
    /** Build the induced subgraph over a subset of this graph's nodes. */
    subgraph(nodeIds) {
        return new MCODEGraph(nodeIds, this.adjacency);
    }
    /**
     * The k-core: the maximal subgraph in which every node has degree >= k.
     * Computed by iteratively removing all nodes whose degree drops below k.
     * Returns null when the k-core is empty.
     */
    getKCore(k, includeLoops) {
        let current = this;
        // Repeatedly peel away low-degree nodes until the set is stable.
        for (;;) {
            const kept = current.nodes.filter((node) => current.degree(node, includeLoops) >= k);
            if (kept.length === 0)
                return null;
            if (kept.length === current.nodeCount)
                break; // stable — every node qualifies
            current = current.subgraph(kept);
        }
        return current;
    }
    /**
     * The highest k-core in the graph: the largest k for which a non-empty
     * k-core exists, together with that core's subgraph.
     * Returns `{ k: 0, graph: null }` for an edgeless graph.
     */
    getHighestKCore(includeLoops) {
        let k = 1;
        let previous = null;
        for (;;) {
            const core = this.getKCore(k, includeLoops);
            if (core === null)
                break;
            previous = core;
            k += 1;
        }
        return { k: k - 1, graph: previous };
    }
}

;// ./src/model/mcodeTypes.ts
/**
 * Type definitions and default parameters for the MCODE algorithm.
 *
 * This is a TypeScript port of the MCODE (Molecular Complex Detection)
 * algorithm by Gary Bader.
 *   - Original paper: Bader GD, Hogue CW. "An automated method for finding
 *     molecular complexes in large protein interaction networks."
 *     BMC Bioinformatics. 2003.
 *   - Original Java source (LGPL v2.1+):
 *     https://github.com/BaderLab/MCODE
 *
 * Ported and adapted under the terms of the GNU Lesser General Public
 * License, version 2.1 or (at your option) any later version.
 */
/** Human-readable labels for each scope (matches the Java enum's toString). */
const MCODE_ANALYSIS_SCOPE_LABELS = {
    NETWORK: 'In Whole Network',
    SELECTION: 'From Selection',
};
/** Default MCODE parameters (match the Cytoscape MCODE app). */
const DEFAULT_MCODE_PARAMETERS = {
    scope: 'NETWORK',
    includeLoops: false,
    degreeCutoff: 2,
    kCore: 2,
    nodeScoreCutoff: 0.2,
    maxDepthFromStart: 100,
    haircut: true,
    fluff: false,
    fluffNodeDensityCutoff: 0.1,
};

;// ./src/model/mcodeAlgorithm.ts
/**
 * MCODE (Molecular Complex Detection) — TypeScript port.
 *
 * Faithful port of BaderLab/MCODE's MCODEAlgorithm.java (LGPL v2.1+):
 *   Bader GD, Hogue CW. "An automated method for finding molecular complexes
 *   in large protein interaction networks." BMC Bioinformatics. 2003.
 *   https://github.com/BaderLab/MCODE
 *
 * Ported and adapted under the GNU Lesser General Public License, version 2.1
 * or (at your option) any later version. See mcodeTypes.ts for attribution.
 *
 * Parallelism note: the original Java implementation scores nodes on a thread
 * pool (one task per node). JavaScript is single-threaded, so the scoring phase
 * here is a sequential loop. The work is embarrassingly parallel and pure, so
 * for very large networks it could be offloaded to Web Workers without changing
 * the results — see scoreGraph() for where the per-node work happens.
 *
 * The algorithm has three stages:
 *   1. scoreGraph    — score every node from its neighborhood k-core & density.
 *   2. findClusters  — grow clusters from high-scoring seeds, then post-process
 *                      (filter by k-core, optional haircut, optional fluff).
 *   3. rank          — sort clusters by descending score.
 */


class MCODEAlgorithm {
    params;
    /** The adjacency the graph was scored from; retained so the scored state can
     *  be snapshotted and rehydrated (the graph is rebuilt from it). */
    adjacency = new Map();
    /** Full input network as an MCODEGraph. Set during scoreGraph(). */
    graph = null;
    /** Per-node cached metrics (density, k-core, score), keyed by node id. */
    nodeInfo = new Map();
    /** Node ids ordered by descending score (seed iteration order). */
    nodesByScoreDesc = [];
    constructor(params = {}) {
        this.params = { ...DEFAULT_MCODE_PARAMETERS, ...params };
    }
    /**
     * Convenience entry point: score the graph and return ranked clusters.
     * `adjacency` is an undirected `nodeId -> neighborIds` map (e.g. built from
     * Cytoscape Web's ElementApi.getConnectedNodes).
     */
    run(adjacency) {
        this.scoreGraph(adjacency);
        return this.findClusters();
    }
    // ── Stage 1: scoring ────────────────────────────────────────────────────────
    /**
     * Compute a NodeInfo (and score) for every node. Equivalent to the Java
     * scoreGraph()/calcNodeInfo()/scoreNode() trio; runs sequentially here.
     */
    scoreGraph(adjacency) {
        this.adjacency = adjacency;
        this.graph = new MCODEGraph(adjacency.keys(), adjacency);
        this.nodeInfo = new Map();
        for (const nodeId of this.graph.nodes) {
            const info = this.calcNodeInfo(nodeId);
            info.score = this.scoreNode(info);
            this.nodeInfo.set(nodeId, info);
        }
        // Order nodes by descending score. Equal-scored nodes keep the graph's node
        // order (i.e. the source network's node order), matching the Java
        // implementation, which seeds tied nodes in network node-list order. Array
        // sort is stable (ES2019+), so returning 0 for ties preserves that order —
        // do NOT tie-break by node id, since the seed must follow network order.
        this.nodesByScoreDesc = [...this.graph.nodes].sort((a, b) => this.scoreOf(b) - this.scoreOf(a));
    }
    /**
     * Per-node metrics: neighborhood density and the density of the
     * neighborhood's highest k-core. Mirrors calcNodeInfo().
     */
    calcNodeInfo(nodeId) {
        const graph = this.requireGraph();
        const neighbors = graph.neighbors(nodeId);
        const numNeighbors = neighbors.length;
        // A node needs at least two neighbors to form a meaningful core.
        if (numNeighbors < 2) {
            const trivial = numNeighbors === 1;
            return {
                density: trivial ? 1 : 0,
                // Neighborhood size includes the node itself (matches the Java impl).
                numNodeNeighbors: numNeighbors + 1,
                nodeNeighbors: neighbors,
                coreLevel: trivial ? 1 : 0,
                coreDensity: trivial ? 1 : 0,
                score: 0,
            };
        }
        // Neighborhood subgraph = the node plus all of its neighbors.
        const neighborhood = graph.subgraph([nodeId, ...neighbors]);
        const density = neighborhood.density(this.params.includeLoops);
        const { k, graph: coreGraph } = neighborhood.getHighestKCore(this.params.includeLoops);
        const coreDensity = coreGraph !== null ? coreGraph.density(this.params.includeLoops) : 0;
        return {
            density,
            // Neighborhood size includes the node itself (matches the Java impl).
            numNodeNeighbors: numNeighbors + 1,
            nodeNeighbors: neighbors,
            coreLevel: k,
            coreDensity,
            score: 0,
        };
    }
    /** Node score = coreDensity * coreLevel, or 0 below the degree cutoff. */
    scoreNode(info) {
        if (info.numNodeNeighbors > this.params.degreeCutoff) {
            return info.coreDensity * info.coreLevel;
        }
        return 0;
    }
    // ── Stage 2: cluster finding ────────────────────────────────────────────────
    /**
     * Grow clusters from seed nodes in descending score order, then filter,
     * haircut and fluff. Mirrors findClusters().
     */
    findClusters() {
        const graph = this.requireGraph();
        const clusters = [];
        // Tracks nodes already consumed as cluster cores so they cannot seed again.
        const nodeSeen = new Set();
        for (const seedId of this.nodesByScoreDesc) {
            if (nodeSeen.has(seedId))
                continue;
            // Only positively-scored nodes can seed a cluster.
            if (this.scoreOf(seedId) <= 0)
                continue;
            // Snapshot the nodes already claimed by higher-ranked clusters (taken
            // before this cluster expands) so exploreCluster() can preserve their
            // priority when shrinking this cluster later.
            const nodeSeenSnapshot = [...nodeSeen];
            const coreNodes = this.getClusterCore(seedId, nodeSeen, this.params.nodeScoreCutoff, this.params.maxDepthFromStart);
            if (coreNodes.length === 0)
                continue;
            let clusterGraph = graph.subgraph(coreNodes);
            // Filter: the cluster must contain at least the required k-core.
            if (this.filterCluster(clusterGraph))
                continue;
            let nodes = coreNodes;
            // Haircut: reduce to the 2-core, dropping degree-1 pendant nodes.
            if (this.params.haircut) {
                nodes = this.haircutCluster(clusterGraph);
                clusterGraph = graph.subgraph(nodes);
            }
            // Fluff: add back dense peripheral neighbors (not marked globally seen).
            if (this.params.fluff) {
                nodes = this.fluffCluster(nodes, nodeSeen);
                clusterGraph = graph.subgraph(nodes);
            }
            clusters.push({
                seedId,
                nodes,
                score: this.scoreCluster(clusterGraph),
                rank: 0, // assigned by rank()
                nodeSeenSnapshot,
            });
        }
        return this.rank(clusters);
    }
    /**
     * Re-grow a single cluster from its seed using a different node-score cutoff,
     * reusing the cached node scoring (no rescoring). Mirrors the Java
     * exploreCluster(): unlike findClusters there is NO k-core filter, so the
     * cluster can shrink all the way to a single node.
     *
     * Returns a NEW cluster (the input is not mutated). `seedId` and `rank` are
     * preserved; `nodes` and `score` are recomputed; `nodePositions` is left unset
     * so the caller's thumbnail regenerates its layout. Because it re-expands from
     * the seed (not from the cluster's current nodes), it is idempotent for a
     * given cutoff.
     */
    exploreCluster(cluster, nodeScoreCutoff) {
        const graph = this.requireGraph();
        const params = this.params;
        // At or below the original cutoff, respect the nodes already claimed by
        // higher-ranked clusters (keeps their priority); above it, let the cluster
        // accrue nodes freely.
        const nodeSeen = nodeScoreCutoff <= params.nodeScoreCutoff
            ? new Set(cluster.nodeSeenSnapshot ?? [])
            : new Set();
        const { seedId } = cluster;
        let nodes = this.getClusterCore(seedId, nodeSeen, nodeScoreCutoff, params.maxDepthFromStart);
        if (!nodes.includes(seedId))
            nodes.push(seedId);
        let clusterGraph = graph.subgraph(nodes);
        if (params.haircut) {
            nodes = this.haircutCluster(clusterGraph);
            clusterGraph = graph.subgraph(nodes);
        }
        if (params.fluff) {
            nodes = this.fluffCluster(nodes, nodeSeen);
            clusterGraph = graph.subgraph(nodes);
        }
        return {
            seedId,
            nodes,
            score: this.scoreCluster(clusterGraph),
            rank: cluster.rank,
            nodeScoreCutoff,
            nodeSeenSnapshot: cluster.nodeSeenSnapshot,
        };
    }
    /**
     * Build the list of nodes forming a cluster core grown from `seedId`.
     * Mirrors getClusterCore(): the seed is included, then neighbors are added
     * recursively when their score clears the seed-relative threshold.
     */
    getClusterCore(seedId, nodeSeen, nodeScoreCutoff, maxDepthFromStart) {
        const cluster = [seedId];
        const seedScore = this.scoreOf(seedId);
        this.getClusterCoreInternal(seedId, nodeSeen, seedScore, 1, cluster, nodeScoreCutoff, maxDepthFromStart);
        return cluster;
    }
    /**
     * Recursive neighbor expansion. Mirrors getClusterCoreInternal().
     * `seedScore` is the reference score of the original seed and stays constant
     * across the recursion; a neighbor qualifies when
     *   score(neighbor) >= seedScore * (1 - nodeScoreCutoff).
     */
    getClusterCoreInternal(startId, nodeSeen, seedScore, depth, cluster, nodeScoreCutoff, maxDepthFromStart) {
        if (nodeSeen.has(startId))
            return;
        if (depth > maxDepthFromStart)
            return;
        nodeSeen.add(startId);
        const threshold = seedScore * (1 - nodeScoreCutoff);
        const info = this.nodeInfo.get(startId);
        if (info === undefined)
            return;
        for (const neighbor of info.nodeNeighbors) {
            if (nodeSeen.has(neighbor))
                continue;
            if (this.scoreOf(neighbor) >= threshold) {
                cluster.push(neighbor);
                this.getClusterCoreInternal(neighbor, nodeSeen, seedScore, depth + 1, cluster, nodeScoreCutoff, maxDepthFromStart);
            }
        }
    }
    // ── Stage 2 post-processing ─────────────────────────────────────────────────
    /**
     * Returns true when the cluster should be discarded: it must contain a
     * non-empty k-core of size `params.kCore`. Mirrors filterCluster().
     */
    filterCluster(clusterGraph) {
        if (clusterGraph.nodeCount === 0)
            return true;
        const core = clusterGraph.getKCore(this.params.kCore, this.params.includeLoops);
        return core === null;
    }
    /**
     * Haircut: reduce the cluster to its 2-core, removing degree-1 pendant
     * nodes. Falls back to the original nodes if no 2-core exists.
     * Mirrors haircutCluster().
     */
    haircutCluster(clusterGraph) {
        const core = clusterGraph.getKCore(2, this.params.includeLoops);
        return core !== null ? core.nodes : clusterGraph.nodes;
    }
    /**
     * Fluff: add neighbors of the cluster whose own neighborhood density exceeds
     * `fluffNodeDensityCutoff`. Fluffed nodes are NOT added to the global
     * nodeSeen set, so they may also appear in other clusters.
     * Mirrors fluffClusterBoundary().
     */
    fluffCluster(nodes, nodeSeen) {
        const result = [...nodes];
        const inCluster = new Set(nodes);
        const addedDuringFluff = new Set();
        for (const nodeId of nodes) {
            const info = this.nodeInfo.get(nodeId);
            if (info === undefined)
                continue;
            for (const neighbor of info.nodeNeighbors) {
                if (inCluster.has(neighbor))
                    continue;
                if (nodeSeen.has(neighbor))
                    continue;
                if (addedDuringFluff.has(neighbor))
                    continue;
                const neighborInfo = this.nodeInfo.get(neighbor);
                if (neighborInfo !== undefined &&
                    neighborInfo.density > this.params.fluffNodeDensityCutoff) {
                    result.push(neighbor);
                    addedDuringFluff.add(neighbor);
                }
            }
        }
        return result;
    }
    // ── Stage 3: scoring & ranking ──────────────────────────────────────────────
    /** Cluster score = density * nodeCount. Mirrors scoreCluster(). */
    scoreCluster(clusterGraph) {
        return clusterGraph.density(this.params.includeLoops) * clusterGraph.nodeCount;
    }
    /** Sort clusters by descending score and assign 1-based ranks. */
    rank(clusters) {
        clusters.sort((a, b) => b.score - a.score);
        clusters.forEach((cluster, index) => {
            cluster.rank = index + 1;
        });
        return clusters;
    }
    // ── Public accessors ────────────────────────────────────────────────────────
    /** The parameters this algorithm was configured with. */
    getParameters() {
        return this.params;
    }
    /** Score assigned to a node during scoreGraph(); 0 if the node is unknown. */
    getNodeScore(nodeId) {
        return this.scoreOf(nodeId);
    }
    /** Cached metrics for a node, or undefined if it was never scored. */
    getNodeInfo(nodeId) {
        return this.nodeInfo.get(nodeId);
    }
    /** Every scored node's score, keyed by node id. */
    getScores() {
        const scores = {};
        for (const [nodeId, info] of this.nodeInfo)
            scores[nodeId] = info.score;
        return scores;
    }
    // ── Serialization ───────────────────────────────────────────────────────────
    /**
     * Capture the scored state into a structured-cloneable snapshot, so the
     * algorithm can be transferred out of the web worker. Rehydrate it on the
     * main thread with fromSnapshot().
     */
    toSnapshot() {
        return {
            params: this.params,
            adjacency: this.adjacency,
            nodeInfo: this.nodeInfo,
            nodesByScoreDesc: this.nodesByScoreDesc,
        };
    }
    /**
     * Reconstruct an algorithm from a snapshot. The graph is rebuilt from the
     * adjacency, and the cached node metrics + seed order are restored as-is, so
     * findClusters() (and future cluster-exploration) can run again without
     * recomputing the expensive per-node scoring.
     */
    static fromSnapshot(snapshot) {
        const alg = new MCODEAlgorithm(snapshot.params);
        alg.adjacency = snapshot.adjacency;
        alg.graph = new MCODEGraph(snapshot.adjacency.keys(), snapshot.adjacency);
        alg.nodeInfo = snapshot.nodeInfo;
        alg.nodesByScoreDesc = snapshot.nodesByScoreDesc;
        return alg;
    }
    // ── Helpers ─────────────────────────────────────────────────────────────────
    scoreOf(nodeId) {
        return this.nodeInfo.get(nodeId)?.score ?? 0;
    }
    requireGraph() {
        if (this.graph === null) {
            throw new Error('scoreGraph() must be called before findClusters()');
        }
        return this.graph;
    }
}

;// ./src/model/useMcodeWorker.ts
/**
 * React hook that owns a single MCODE web worker and exposes a promise-based
 * `run()` for executing an analysis off the main thread, plus a `cancel()` to
 * abort the one in progress.
 *
 * The worker is created lazily on first use and terminated when the consuming
 * component unmounts. Only one analysis may be in flight at a time (the caller
 * is expected to guard the UI accordingly); a second concurrent `run()` rejects.
 *
 * ── Why a Web Worker? ───────────────────────────────────────────────────────
 * MCODE clustering is heavy, synchronous, CPU-bound work (per-node k-core /
 * density scoring, then cluster finding) with nothing to await — it just
 * occupies the thread until it finishes. JavaScript is single-threaded, and the
 * main thread is shared with rendering and input, so running it inline freezes
 * the UI for the whole duration.
 *
 * That's especially bad here because this app is a Module Federation remote
 * embedded in Cytoscape Web: a blocked main thread freezes the *host* app, not
 * just our panel. Offloading to a worker keeps the main thread free, which buys:
 *   - no freeze: large networks take seconds, but the UI stays live;
 *   - a real progress spinner and a working Cancel button (we just terminate()
 *     the worker — you can't reliably cancel synchronous main-thread work).
 *
 * It's a clean fit because the algorithm is pure: it operates on a plain
 * adjacency map with no DOM / React / cyweb dependencies, so the worker bundle
 * contains only the algorithm.
 *
 * Trade-offs we accept: inputs/outputs cross by structured-clone copy via
 * postMessage (fine — they're plain/cloneable), and because the algorithm
 * instance lives in the worker, its scored state is returned as a serializable
 * snapshot and rehydrated on the main thread (see MCODEAlgorithm.toSnapshot /
 * fromSnapshot) so features like cluster exploration can reuse it without
 * rescoring. If analyses were always tiny this would be over-engineering, but
 * real MCODE runs block long enough — and freezing the host raises the stakes —
 * to make it worth the message-passing overhead.
 */


/** Rejection raised when an in-flight analysis is cancelled by the user. */
class McodeCancelledError extends Error {
    constructor() {
        super('MCODE analysis was cancelled');
        this.name = 'McodeCancelledError';
    }
}
/**
 * Resolve the absolute URL of the webpack-emitted MCODE worker chunk.
 *
 * webpack rewrites `new Worker(new URL('./mcode.worker.ts', import.meta.url))`
 * at build time: it emits the worker as a self-contained classic-worker chunk
 * and fills in the chunk's absolute URL (derived from the runtime publicPath).
 * That URL is only produced *inside* the `new Worker(...)` expression — a bare
 * `new URL(...)` instead emits the raw, uncompiled `.ts` source.
 *
 * To read the URL without actually constructing the worker (which would throw
 * cross-origin — see createMcodeWorker), we briefly swap in a stub `Worker`
 * that just records its first argument. The swap is synchronous and restored in
 * `finally`, so nothing else can observe it.
 *
 * The `{ name }` option pins the worker's chunk filename (e.g. `mcode-worker.js`)
 * instead of a chunk-id-derived name. That keeps the URL stable when unrelated
 * changes shift webpack's chunk ids — otherwise the dev server's worker child
 * compilation can desync and serve a 404 for the captured URL.
 */
function resolveWorkerChunkUrl() {
    const RealWorker = globalThis.Worker;
    let capturedUrl = '';
    globalThis.Worker = class {
        constructor(scriptUrl) {
            capturedUrl = String(scriptUrl);
        }
    };
    try {
        // The 'mcode-worker' name is load-bearing: webpack.config.js's
        // optimization.splitChunks excludes this chunk name from splitting so the
        // worker stays self-contained (it's loaded via a cross-origin blob and can't
        // fetch sibling chunks). Keep the two in sync if you rename it.
        // eslint-disable-next-line no-new
        new Worker(new URL(/* worker import */ __webpack_require__.p + __webpack_require__.u(178), __webpack_require__.b), { name: 'mcode-worker', type: "module" });
    }
    finally {
        globalThis.Worker = RealWorker;
    }
    return capturedUrl;
}
/**
 * Construct the MCODE worker.
 *
 * When this app runs as a Module Federation remote, the worker chunk is served
 * from the remote's own origin (e.g. the plugin dev server on :5555), which
 * differs from the host page's origin (e.g. cyweb on :5500). Browsers forbid
 * constructing a `Worker` directly from a cross-origin script, so we wrap it in
 * a tiny same-origin Blob that `importScripts()` the real worker URL — classic
 * workers may `importScripts` cross-origin (the remote serves assets with
 * `Access-Control-Allow-Origin: *`). This path also works unchanged same-origin.
 */
function createMcodeWorker() {
    const workerUrl = resolveWorkerChunkUrl();
    // Log the resolved URL so it can be checked directly (browser Network tab /
    // curl) when diagnosing load failures.
    console.debug(`Creating MCODE worker from: ${workerUrl}`);
    const bootstrap = `importScripts(${JSON.stringify(workerUrl)})`;
    const blobUrl = URL.createObjectURL(new Blob([bootstrap], { type: 'application/javascript' }));
    try {
        const worker = new Worker(blobUrl);
        // A failed importScripts of the (cross-origin) worker chunk surfaces here as
        // an often-opaque error event. Echo the URL and a hint, since the event
        // message is usually empty for cross-origin worker load failures. (The
        // hook's onerror handler is what actually rejects the pending analysis.)
        worker.addEventListener('error', (event) => {
            console.error(`MCODE worker failed to load from "${workerUrl}". ` +
                'Check that the dev server serves this exact URL (HTTP 200) — a stale ' +
                'dev server usually needs a full restart, not just HMR. ' +
                `Worker error: ${event.message || '(no message; likely a cross-origin load failure)'}`);
        });
        return worker;
    }
    finally {
        // The Worker has already fetched the bootstrap script; the blob URL can go.
        URL.revokeObjectURL(blobUrl);
    }
}
function useMcodeWorker() {
    const workerRef = (0,consume_shared_module_default_react_1_8_3_singleton_.useRef)(null);
    const pendingRef = (0,consume_shared_module_default_react_1_8_3_singleton_.useRef)(null);
    // Settle the in-flight promise (if any) and clear it.
    const settle = (0,consume_shared_module_default_react_1_8_3_singleton_.useRef)((response) => {
        const pending = pendingRef.current;
        pendingRef.current = null;
        if (!pending)
            return;
        if (response instanceof Error)
            pending.reject(response);
        else if (response.type === 'success')
            pending.resolve({
                clusters: response.clusters,
                algorithm: MCODEAlgorithm.fromSnapshot(response.snapshot),
            });
        else
            pending.reject(new Error(response.message));
    });
    // Lazily create the worker and wire up its handlers.
    const getWorker = (0,consume_shared_module_default_react_1_8_3_singleton_.useCallback)(() => {
        if (workerRef.current === null) {
            const worker = createMcodeWorker();
            worker.onmessage = (event) => settle.current(event.data);
            worker.onerror = (event) => settle.current(new Error(event.message || 'MCODE worker crashed'));
            workerRef.current = worker;
        }
        return workerRef.current;
    }, []);
    // Tear the worker down on unmount; reject any analysis still running.
    (0,consume_shared_module_default_react_1_8_3_singleton_.useEffect)(() => {
        return () => {
            settle.current(new Error('MCODE worker was terminated'));
            workerRef.current?.terminate();
            workerRef.current = null;
        };
    }, []);
    const run = (0,consume_shared_module_default_react_1_8_3_singleton_.useCallback)((adjacency, parameters) => new Promise((resolve, reject) => {
        if (pendingRef.current) {
            reject(new Error('An MCODE analysis is already running'));
            return;
        }
        try {
            const worker = getWorker();
            pendingRef.current = { resolve, reject };
            const request = { adjacency, parameters };
            worker.postMessage(request);
        }
        catch (err) {
            pendingRef.current = null;
            reject(err instanceof Error ? err : new Error(String(err)));
        }
    }), [getWorker]);
    const cancel = (0,consume_shared_module_default_react_1_8_3_singleton_.useCallback)(() => {
        if (pendingRef.current === null)
            return;
        // Reject the in-flight analysis and dispose the worker. A terminated worker
        // can't be reused, so the next run() lazily creates a fresh one.
        settle.current(new McodeCancelledError());
        workerRef.current?.terminate();
        workerRef.current = null;
    }, []);
    return { run, cancel };
}

;// ./src/components/NewAnalysisDialog.tsx




/**
 * Validate a single integer field that must be strictly greater than `min`.
 * Returns an error message, or undefined when the value is valid.
 */
const validateIntGreaterThan = (raw, min, label) => {
    const value = Number(raw);
    if (raw.trim() === '' || !Number.isInteger(value) || value <= min)
        return `The ${label} must be greater than ${min}.`;
    return undefined;
};
/**
 * Validate a single fraction field that must lie within [0, 1] inclusive.
 * Returns an error message, or undefined when the value is valid.
 */
const validateFraction = (raw, label) => {
    const value = Number(raw);
    if (raw.trim() === '' || Number.isNaN(value) || value < 0 || value > 1)
        return `The ${label} must be between 0 and 1.`;
    return undefined;
};
const NewAnalysisDialog = ({ networkId, open, onClose, onSubmit, }) => {
    // Scope and the two boolean options are stored as their final types; the
    // numeric inputs are kept as strings so the user can type freely (and we
    // can surface validation messages) before parsing on submit.
    const [scope, setScope] = (0,consume_shared_module_default_react_1_8_3_singleton_.useState)(DEFAULT_MCODE_PARAMETERS.scope);
    const [includeLoops, setIncludeLoops] = (0,consume_shared_module_default_react_1_8_3_singleton_.useState)(DEFAULT_MCODE_PARAMETERS.includeLoops);
    const [haircut, setHaircut] = (0,consume_shared_module_default_react_1_8_3_singleton_.useState)(DEFAULT_MCODE_PARAMETERS.haircut);
    const [fluff, setFluff] = (0,consume_shared_module_default_react_1_8_3_singleton_.useState)(DEFAULT_MCODE_PARAMETERS.fluff);
    const [degreeCutoff, setDegreeCutoff] = (0,consume_shared_module_default_react_1_8_3_singleton_.useState)(String(DEFAULT_MCODE_PARAMETERS.degreeCutoff));
    const [nodeScoreCutoff, setNodeScoreCutoff] = (0,consume_shared_module_default_react_1_8_3_singleton_.useState)(String(DEFAULT_MCODE_PARAMETERS.nodeScoreCutoff));
    const [kCore, setKCore] = (0,consume_shared_module_default_react_1_8_3_singleton_.useState)(String(DEFAULT_MCODE_PARAMETERS.kCore));
    const [maxDepthFromStart, setMaxDepthFromStart] = (0,consume_shared_module_default_react_1_8_3_singleton_.useState)(String(DEFAULT_MCODE_PARAMETERS.maxDepthFromStart));
    const [fluffNodeDensityCutoff, setFluffNodeDensityCutoff] = (0,consume_shared_module_default_react_1_8_3_singleton_.useState)(String(DEFAULT_MCODE_PARAMETERS.fluffNodeDensityCutoff));
    const [errors, setErrors] = (0,consume_shared_module_default_react_1_8_3_singleton_.useState)({});
    // Reset every field back to the defaults each time the dialog is (re)opened,
    // since the component stays mounted between openings.
    (0,consume_shared_module_default_react_1_8_3_singleton_.useEffect)(() => {
        if (!open)
            return;
        setScope(DEFAULT_MCODE_PARAMETERS.scope);
        setIncludeLoops(DEFAULT_MCODE_PARAMETERS.includeLoops);
        setHaircut(DEFAULT_MCODE_PARAMETERS.haircut);
        setFluff(DEFAULT_MCODE_PARAMETERS.fluff);
        setDegreeCutoff(String(DEFAULT_MCODE_PARAMETERS.degreeCutoff));
        setNodeScoreCutoff(String(DEFAULT_MCODE_PARAMETERS.nodeScoreCutoff));
        setKCore(String(DEFAULT_MCODE_PARAMETERS.kCore));
        setMaxDepthFromStart(String(DEFAULT_MCODE_PARAMETERS.maxDepthFromStart));
        setFluffNodeDensityCutoff(String(DEFAULT_MCODE_PARAMETERS.fluffNodeDensityCutoff));
        setErrors({});
    }, [open]);
    /**
     * Run every consistency check (mirroring the Java FormattedTextFieldAction
     * bounds) and return the resulting error map. The density cutoff is only
     * checked when fluffing is enabled, since it is otherwise ignored.
     */
    const validate = () => {
        const next = {};
        next.degreeCutoff = validateIntGreaterThan(degreeCutoff, 1, 'degree cutoff');
        next.nodeScoreCutoff = validateFraction(nodeScoreCutoff, 'node score cutoff');
        next.kCore = validateIntGreaterThan(kCore, 1, 'K-Core');
        next.maxDepthFromStart = validateIntGreaterThan(maxDepthFromStart, 0, 'maximum depth');
        if (fluff)
            next.fluffNodeDensityCutoff = validateFraction(fluffNodeDensityCutoff, 'fluff node density cutoff');
        Object.keys(next).forEach((k) => next[k] === undefined && delete next[k]);
        return next;
    };
    const handleSubmit = () => {
        const found = validate();
        setErrors(found);
        if (Object.keys(found).length > 0)
            return;
        const parameters = {
            scope,
            includeLoops,
            degreeCutoff: Number(degreeCutoff),
            kCore: Number(kCore),
            nodeScoreCutoff: Number(nodeScoreCutoff),
            maxDepthFromStart: Number(maxDepthFromStart),
            haircut,
            fluff,
            fluffNodeDensityCutoff: Number(fluffNodeDensityCutoff),
        };
        onClose();
        onSubmit(parameters);
    };
    // Shared props for the small, right-aligned numeric text fields.
    const numberFieldSx = { width: 90 };
    return ((0,jsx_runtime.jsxs)(material_5_1_8_singleton_.Dialog, { open: open, maxWidth: "xs", fullWidth: true, children: [(0,jsx_runtime.jsx)(material_5_1_8_singleton_.DialogTitle, { children: "New MCODE Analysis" }), (0,jsx_runtime.jsx)(material_5_1_8_singleton_.DialogContent, { children: (0,jsx_runtime.jsxs)(material_5_1_8_singleton_.Box, { sx: { display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }, children: [(0,jsx_runtime.jsxs)(material_5_1_8_singleton_.FormControl, { component: "fieldset", sx: { border: (t) => `1px solid ${t.palette.divider}`, borderRadius: 1, px: 2, py: 1 }, children: [(0,jsx_runtime.jsx)(material_5_1_8_singleton_.FormLabel, { component: "legend", sx: { px: 0.5 }, children: "Find Clusters" }), (0,jsx_runtime.jsx)(material_5_1_8_singleton_.RadioGroup, { value: scope, onChange: (e) => setScope(e.target.value), children: Object.keys(MCODE_ANALYSIS_SCOPE_LABELS).map((value) => ((0,jsx_runtime.jsx)(material_5_1_8_singleton_.FormControlLabel, { value: value, control: (0,jsx_runtime.jsx)(material_5_1_8_singleton_.Radio, { size: "small" }), label: MCODE_ANALYSIS_SCOPE_LABELS[value] }, value))) })] }), (0,jsx_runtime.jsxs)(material_5_1_8_singleton_.Box, { component: "fieldset", sx: { border: (t) => `1px solid ${t.palette.divider}`, borderRadius: 1, px: 2, py: 1, m: 0 }, children: [(0,jsx_runtime.jsx)(material_5_1_8_singleton_.Typography, { component: "legend", variant: "subtitle2", sx: { px: 0.5 }, children: "Network Scoring" }), (0,jsx_runtime.jsx)(material_5_1_8_singleton_.Tooltip, { title: "Self-edges may increase a node's score slightly.", children: (0,jsx_runtime.jsx)(material_5_1_8_singleton_.FormControlLabel, { control: (0,jsx_runtime.jsx)(material_5_1_8_singleton_.Checkbox, { size: "small", checked: includeLoops, onChange: (e) => setIncludeLoops(e.target.checked) }), label: "Include Loops" }) }), (0,jsx_runtime.jsxs)(material_5_1_8_singleton_.Box, { sx: { display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', mt: 1 }, children: [(0,jsx_runtime.jsx)(material_5_1_8_singleton_.Typography, { variant: "body2", sx: { mt: 1 }, children: "Degree Cutoff:" }), (0,jsx_runtime.jsx)(material_5_1_8_singleton_.Tooltip, { title: "Sets the minimum number of edges for a node to be scored.", children: (0,jsx_runtime.jsx)(material_5_1_8_singleton_.TextField, { size: "small", type: "number", value: degreeCutoff, onChange: (e) => setDegreeCutoff(e.target.value), onBlur: () => setErrors((p) => ({ ...p, degreeCutoff: validateIntGreaterThan(degreeCutoff, 1, 'degree cutoff') })), error: Boolean(errors.degreeCutoff), helperText: errors.degreeCutoff, sx: numberFieldSx }) })] })] }), (0,jsx_runtime.jsxs)(material_5_1_8_singleton_.Box, { component: "fieldset", sx: { border: (t) => `1px solid ${t.palette.divider}`, borderRadius: 1, px: 2, py: 1, m: 0 }, children: [(0,jsx_runtime.jsx)(material_5_1_8_singleton_.Typography, { component: "legend", variant: "subtitle2", sx: { px: 0.5 }, children: "Cluster Finding" }), (0,jsx_runtime.jsxs)(material_5_1_8_singleton_.Box, { sx: { display: 'flex', flexDirection: 'column' }, children: [(0,jsx_runtime.jsx)(material_5_1_8_singleton_.Tooltip, { title: "Remove singly connected nodes from clusters.", children: (0,jsx_runtime.jsx)(material_5_1_8_singleton_.FormControlLabel, { control: (0,jsx_runtime.jsx)(material_5_1_8_singleton_.Checkbox, { size: "small", checked: haircut, onChange: (e) => setHaircut(e.target.checked) }), label: "Haircut" }) }), (0,jsx_runtime.jsx)(material_5_1_8_singleton_.Tooltip, { title: "Expand core cluster by one neighbour shell (applied after the optional haircut).", children: (0,jsx_runtime.jsx)(material_5_1_8_singleton_.FormControlLabel, { control: (0,jsx_runtime.jsx)(material_5_1_8_singleton_.Checkbox, { size: "small", checked: fluff, onChange: (e) => setFluff(e.target.checked) }), label: "Fluff" }) })] }), (0,jsx_runtime.jsxs)(material_5_1_8_singleton_.Box, { sx: { display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', mt: 1 }, children: [(0,jsx_runtime.jsx)(material_5_1_8_singleton_.Typography, { variant: "body2", sx: { mt: 1 }, color: fluff ? 'text.primary' : 'text.disabled', children: "Node Density Cutoff:" }), (0,jsx_runtime.jsx)(material_5_1_8_singleton_.Tooltip, { title: "Limits fluffing by setting the acceptable node density deviance from the core cluster density (allows clusters' edges to overlap).", children: (0,jsx_runtime.jsx)(material_5_1_8_singleton_.TextField, { size: "small", type: "number", disabled: !fluff, value: fluffNodeDensityCutoff, onChange: (e) => setFluffNodeDensityCutoff(e.target.value), onBlur: () => setErrors((p) => ({ ...p, fluffNodeDensityCutoff: fluff ? validateFraction(fluffNodeDensityCutoff, 'fluff node density cutoff') : undefined })), error: Boolean(errors.fluffNodeDensityCutoff), helperText: errors.fluffNodeDensityCutoff, inputProps: { step: 0.001 }, sx: numberFieldSx }) })] }), (0,jsx_runtime.jsxs)(material_5_1_8_singleton_.Box, { sx: { display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', mt: 1 }, children: [(0,jsx_runtime.jsx)(material_5_1_8_singleton_.Typography, { variant: "body2", sx: { mt: 1 }, children: "Node Score Cutoff:" }), (0,jsx_runtime.jsx)(material_5_1_8_singleton_.Tooltip, { title: "Sets the acceptable score deviance from the seed node's score for expanding a cluster (most influential parameter for cluster size).", children: (0,jsx_runtime.jsx)(material_5_1_8_singleton_.TextField, { size: "small", type: "number", value: nodeScoreCutoff, onChange: (e) => setNodeScoreCutoff(e.target.value), onBlur: () => setErrors((p) => ({ ...p, nodeScoreCutoff: validateFraction(nodeScoreCutoff, 'node score cutoff') })), error: Boolean(errors.nodeScoreCutoff), helperText: errors.nodeScoreCutoff, inputProps: { step: 0.001 }, sx: numberFieldSx }) })] }), (0,jsx_runtime.jsxs)(material_5_1_8_singleton_.Box, { sx: { display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', mt: 1 }, children: [(0,jsx_runtime.jsx)(material_5_1_8_singleton_.Typography, { variant: "body2", sx: { mt: 1 }, children: "K-Core:" }), (0,jsx_runtime.jsx)(material_5_1_8_singleton_.Tooltip, { title: "Filters out clusters lacking a maximally inter-connected core of at least k edges per node.", children: (0,jsx_runtime.jsx)(material_5_1_8_singleton_.TextField, { size: "small", type: "number", value: kCore, onChange: (e) => setKCore(e.target.value), onBlur: () => setErrors((p) => ({ ...p, kCore: validateIntGreaterThan(kCore, 1, 'K-Core') })), error: Boolean(errors.kCore), helperText: errors.kCore, sx: numberFieldSx }) })] }), (0,jsx_runtime.jsxs)(material_5_1_8_singleton_.Box, { sx: { display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', mt: 1 }, children: [(0,jsx_runtime.jsx)(material_5_1_8_singleton_.Typography, { variant: "body2", sx: { mt: 1 }, children: "Max. Depth:" }), (0,jsx_runtime.jsx)(material_5_1_8_singleton_.Tooltip, { title: "Limits the cluster size by setting the maximum search distance from a seed node (100 virtually means no limit).", children: (0,jsx_runtime.jsx)(material_5_1_8_singleton_.TextField, { size: "small", type: "number", value: maxDepthFromStart, onChange: (e) => setMaxDepthFromStart(e.target.value), onBlur: () => setErrors((p) => ({ ...p, maxDepthFromStart: validateIntGreaterThan(maxDepthFromStart, 0, 'maximum depth') })), error: Boolean(errors.maxDepthFromStart), helperText: errors.maxDepthFromStart, sx: numberFieldSx }) })] })] })] }) }), (0,jsx_runtime.jsxs)(material_5_1_8_singleton_.DialogActions, { children: [(0,jsx_runtime.jsx)(material_5_1_8_singleton_.Button, { onClick: onClose, variant: "outlined", children: "Cancel" }), (0,jsx_runtime.jsx)(material_5_1_8_singleton_.Button, { onClick: handleSubmit, variant: "contained", children: "Analyze Current Network" })] })] }));
};
/* harmony default export */ const components_NewAnalysisDialog = ((/* unused pure expression or super */ null && (NewAnalysisDialog)));

;// ./src/components/MCODEPanel.tsx






















cytoscape_esm/* default */.A.use((cytoscape_euler_default()));
/** Clusters larger than this aren't rendered as thumbnails (layout is too slow). */
const MAX_VISUALIZABLE_CLUSTER_SIZE = 500;
/** Whether a cluster is too big to render as a thumbnail image. */
const isClusterTooLargeToVisualize = (cluster) => cluster.nodes.length > MAX_VISUALIZABLE_CLUSTER_SIZE;
const OptionsMenu = ({ currentNetworkId, results, selectedResult, selectedCluster, onShowAnalysisParameters, onDiscardSelectedResult, onDiscardAllResults, }) => {
    const { viewSourceNetwork, applyMcodeStyle, createClusterNetwork, exportResult } = useMcodeResultActions(selectedResult, selectedCluster);
    const [anchorEl, setAnchorEl] = (0,consume_shared_module_default_react_1_8_3_singleton_.useState)(null);
    const [showParametersResult, setShowParametersResult] = (0,consume_shared_module_default_react_1_8_3_singleton_.useState)(false);
    const [confirmDialogOpen, setConfirmDialogOpen] = (0,consume_shared_module_default_react_1_8_3_singleton_.useState)(false);
    const [confirmMessage, setConfirmMessage] = (0,consume_shared_module_default_react_1_8_3_singleton_.useState)('');
    const [confirmAction, setConfirmAction] = (0,consume_shared_module_default_react_1_8_3_singleton_.useState)(() => { });
    const open = Boolean(anchorEl);
    const handleOptionsClick = (event) => {
        setAnchorEl(event.currentTarget);
    };
    const handleOptionsClose = () => {
        setAnchorEl(null);
    };
    // Menu items close the menu, then run the corresponding result action.
    const handleViewSourceNetwork = () => {
        handleOptionsClose();
        viewSourceNetwork();
    };
    const handleApplyMcodeStyle = () => {
        handleOptionsClose();
        applyMcodeStyle();
    };
    const handleCreateClusterNetwork = () => {
        handleOptionsClose();
        createClusterNetwork();
    };
    const handleExportResult = () => {
        handleOptionsClose();
        exportResult();
    };
    const handleShowAnalysisParameters = () => {
        handleOptionsClose();
        setShowParametersResult((prev) => !prev);
        onShowAnalysisParameters(!showParametersResult);
    };
    const handleDiscardSelectedResult = () => {
        handleOptionsClose();
        if (!selectedResult)
            return;
        setConfirmMessage(`Are you sure you want to discard the result "${selectedResult.name}"?`);
        setConfirmAction(() => onDiscardSelectedResult);
        setConfirmDialogOpen(true);
    };
    const handleDiscardAllResults = () => {
        handleOptionsClose();
        setConfirmMessage('Are you sure you want to discard all results?');
        setConfirmAction(() => onDiscardAllResults);
        setConfirmDialogOpen(true);
    };
    // Actually remove the selected result, after the user confirms.
    const handleConfirmDiscard = () => {
        setConfirmDialogOpen(false);
        confirmAction?.();
    };
    return ((0,jsx_runtime.jsxs)(jsx_runtime.Fragment, { children: [(0,jsx_runtime.jsx)(material_5_1_8_singleton_.Tooltip, { title: "Options...", children: (0,jsx_runtime.jsx)("span", { children: (0,jsx_runtime.jsx)(material_5_1_8_singleton_.IconButton, { onClick: handleOptionsClick, children: (0,jsx_runtime.jsx)(Menu/* default */.A, {}) }) }) }), (0,jsx_runtime.jsxs)(material_5_1_8_singleton_.Menu, { open: open, anchorEl: anchorEl, onClose: handleOptionsClose, anchorOrigin: {
                    vertical: 'bottom',
                    horizontal: 'right',
                }, transformOrigin: {
                    vertical: 'top',
                    horizontal: 'right',
                }, children: [(0,jsx_runtime.jsx)(material_5_1_8_singleton_.MenuItem, { disabled: !selectedResult || currentNetworkId === selectedResult.networkId, onClick: handleViewSourceNetwork, children: (0,jsx_runtime.jsx)(material_5_1_8_singleton_.Typography, { component: "span", sx: { pl: 3.25 }, children: "View Source Network" }) }), (0,jsx_runtime.jsxs)(material_5_1_8_singleton_.MenuItem, { disabled: !selectedResult, onClick: handleApplyMcodeStyle, children: [(0,jsx_runtime.jsx)(Palette/* default */.A, { sx: { ml: 3 } }), (0,jsx_runtime.jsx)(material_5_1_8_singleton_.Typography, { component: "span", sx: { pl: 0.5 }, children: "Apply MCODE Style" })] }), (0,jsx_runtime.jsx)(material_5_1_8_singleton_.Divider, { sx: { my: 0.5 } }), (0,jsx_runtime.jsx)(material_5_1_8_singleton_.MenuItem, { disabled: !selectedCluster, onClick: handleCreateClusterNetwork, children: (0,jsx_runtime.jsx)(material_5_1_8_singleton_.Typography, { component: "span", sx: { pl: 3.25 }, children: "Create Cluster Network" }) }), (0,jsx_runtime.jsxs)(material_5_1_8_singleton_.MenuItem, { disabled: !selectedResult, onClick: handleExportResult, children: [(0,jsx_runtime.jsx)(FileDownload/* default */.A, { sx: { ml: 3 } }), (0,jsx_runtime.jsx)(material_5_1_8_singleton_.Typography, { component: "span", sx: { pl: 0.5 }, children: "Export Result" })] }), (0,jsx_runtime.jsx)(material_5_1_8_singleton_.Divider, { sx: { my: 0.5 } }), (0,jsx_runtime.jsxs)(material_5_1_8_singleton_.MenuItem, { disabled: !selectedResult, onClick: handleShowAnalysisParameters, children: [showParametersResult ? (0,jsx_runtime.jsx)(Check/* default */.A, { fontSize: "small" }) : (0,jsx_runtime.jsx)(material_5_1_8_singleton_.Box, { sx: { width: 24 } }), (0,jsx_runtime.jsx)(Info/* default */.A, {}), (0,jsx_runtime.jsx)(material_5_1_8_singleton_.Typography, { component: "span", sx: { pl: 0.5 }, children: "Show Analysis Parameters" })] }), (0,jsx_runtime.jsx)(material_5_1_8_singleton_.Divider, { sx: { my: 0.5 } }), (0,jsx_runtime.jsxs)(material_5_1_8_singleton_.MenuItem, { disabled: !selectedResult, onClick: handleDiscardSelectedResult, children: [(0,jsx_runtime.jsx)(Delete/* default */.A, { sx: { ml: 3 } }), (0,jsx_runtime.jsx)(material_5_1_8_singleton_.Typography, { component: "span", sx: { pl: 0.5 }, children: "Discard Selected Result" })] }), (0,jsx_runtime.jsxs)(material_5_1_8_singleton_.MenuItem, { disabled: !results || results.length === 0, onClick: handleDiscardAllResults, children: [(0,jsx_runtime.jsx)(Delete/* default */.A, { sx: { ml: 3 } }), (0,jsx_runtime.jsx)(material_5_1_8_singleton_.Typography, { component: "span", sx: { pl: 0.5 }, children: "Discard All Results" })] })] }), (0,jsx_runtime.jsxs)(material_5_1_8_singleton_.Dialog, { open: confirmDialogOpen, onClose: () => setConfirmDialogOpen(false), children: [(0,jsx_runtime.jsx)(material_5_1_8_singleton_.DialogTitle, { children: "Discard Result" }), (0,jsx_runtime.jsx)(material_5_1_8_singleton_.DialogContent, { children: (0,jsx_runtime.jsx)(material_5_1_8_singleton_.DialogContentText, { children: confirmMessage }) }), (0,jsx_runtime.jsxs)(material_5_1_8_singleton_.DialogActions, { children: [(0,jsx_runtime.jsx)(material_5_1_8_singleton_.Button, { onClick: () => setConfirmDialogOpen(false), variant: "outlined", children: "Cancel" }), (0,jsx_runtime.jsx)(material_5_1_8_singleton_.Button, { onClick: handleConfirmDiscard, variant: "contained", color: "error", children: "Confirm" })] })] })] }));
};
const ClusterPanel = (0,consume_shared_module_default_react_1_8_3_singleton_.memo)(({ cluster, edges, algorithm, selected, onClick, onExplore, }) => {
    // Seed from the cached thumbnail so a re-selected result shows it instantly.
    const [status, setStatus] = (0,consume_shared_module_default_react_1_8_3_singleton_.useState)(() => cluster.thumbnail
        ? { kind: 'ready', src: cluster.thumbnail }
        : isClusterTooLargeToVisualize(cluster)
            ? { kind: 'too-large' }
            : { kind: 'loading' });
    // Controlled slider value: the cluster's explored cutoff if any, else the
    // analysis default. Initialized once per mount — the result+seed key on this
    // component remounts it (re-seeding this state) when the user switches results.
    const [cutoff, setCutoff] = (0,consume_shared_module_default_react_1_8_3_singleton_.useState)(cluster.nodeScoreCutoff ?? algorithm.getParameters().nodeScoreCutoff);
    const updateImage = () => {
        if (isClusterTooLargeToVisualize(cluster)) {
            cluster.thumbnail = undefined;
            cluster.nodePositions = undefined;
            setStatus({ kind: 'too-large' });
            return;
        }
        // Keep only the edges whose endpoints are both in the cluster — filtered in
        // memory from the network's pre-fetched edge list (no API calls here).
        const clusterNodes = new Set(cluster.nodes);
        const clusterEdges = edges.filter((e) => clusterNodes.has(e.source) && clusterNodes.has(e.target));
        const elements = [
            ...cluster.nodes.map((id) => ({ data: { id, 'Node Status': cluster.seedId === id ? 'Seed' : 'Clustered' } })),
            ...clusterEdges.map((e) => ({ data: { id: e.id, source: e.source, target: e.target } })),
        ];
        // Cytoscape's canvas renderer needs a sized DOM node, so render into a
        // detached, off-screen container, export the PNG, then tear it down.
        const container = document.createElement('div');
        container.style.position = 'absolute';
        container.style.left = '-9999px';
        container.style.top = '-9999px';
        container.style.width = '200px';
        container.style.height = '200px';
        document.body.appendChild(container);
        const cy = (0,cytoscape_esm/* default */.A)({
            container,
            elements,
            style: [
                {
                    selector: 'node',
                    style: {
                        'background-color': 'rgb(178, 24, 43)',
                        'width': 50,
                        'height': 50,
                        'shape': (n) => n.data('Node Status') === 'Seed' ? 'rectangle' : 'ellipse',
                    },
                },
                {
                    selector: 'edge',
                    style: {
                        'line-color': 'rgb(103, 169, 207)',
                        'width': 5,
                        'curve-style': 'bezier',
                        'target-arrow-color': 'rgb(33, 102, 172)',
                        'target-arrow-shape': 'triangle'
                    },
                },
            ],
            layout: { name: 'euler', animate: false, mass: 25 },
        });
        // `full: true` exports the entire graph fit to the image, independent of
        // viewport zoom/pan. Returns a base64 PNG data URI usable as an <img> src.
        const png = cy.png({ full: true, bg: '#ffffff', scale: 2 });
        // Cache the node positions and the generated image on the cluster so that
        // re-selecting this result reuses them instead of recomputing the layout.
        const nodePositions = {};
        cy.nodes().forEach((n) => {
            const pos = n.position();
            nodePositions[n.id()] = { x: pos.x, y: pos.y };
        });
        cluster.nodePositions = nodePositions;
        cluster.thumbnail = png;
        cy.destroy();
        document.body.removeChild(container);
        setStatus({ kind: 'ready', src: png });
    };
    // Track the thumb live while dragging...
    const handleChange = (event, value) => {
        setCutoff(value);
    };
    // ...and re-grow the cluster only when the drag is released.
    const handleChangeCommitted = (event, value) => {
        setStatus({ kind: 'loading' }); // show the spinner while the new cluster is computed
        setTimeout(() => {
            // Re-grow the cluster at a new node-score cutoff (the size slider) and update the thumbnail.
            const explored = algorithm.exploreCluster(cluster, cutoff);
            cluster.seedId = explored.seedId;
            cluster.nodes = explored.nodes;
            cluster.score = explored.score;
            cluster.nodeScoreCutoff = cutoff;
            cluster.nodeSeenSnapshot = explored.nodeSeenSnapshot;
            updateImage();
            onExplore(cluster, value); // Let the parent know the cluster changed so it can re-select its nodes in the source network
        }, 500); // Give the spinner a chance to render before the CPU hog
    };
    (0,consume_shared_module_default_react_1_8_3_singleton_.useEffect)(() => {
        // Reuse the cached thumbnail if this cluster already has one. It survives
        // result switches (clusters live in component state); exploration makes a
        // new cluster object with no thumbnail, so that one regenerates.
        if (cluster.thumbnail) {
            setStatus({ kind: 'ready', src: cluster.thumbnail });
            return;
        }
        if (cluster.nodes.length === 0) {
            setStatus({ kind: 'loading' });
            return;
        }
        updateImage();
    }, [cluster, edges]);
    return ((0,jsx_runtime.jsx)(material_5_1_8_singleton_.Box, { onClick: () => onClick(cluster), sx: {
            px: 2,
            py: 0.5,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            cursor: 'pointer',
            bgcolor: selected ? 'action.selected' : 'background.paper',
            borderBottom: (theme) => `2px solid ${theme.palette.background.default}`,
        }, children: (0,jsx_runtime.jsxs)(material_5_1_8_singleton_.Box, { sx: {
                display: 'flex',
                alignItems: 'center',
                gap: 2,
                flexGrow: 1,
            }, children: [(0,jsx_runtime.jsx)(material_5_1_8_singleton_.Typography, { variant: "body1", sx: {
                        textAlign: 'right',
                        width: 32,
                        flexShrink: 0,
                        color: 'text.secondary',
                        fontWeight: 'bold',
                    }, children: cluster.rank }), (0,jsx_runtime.jsx)(material_5_1_8_singleton_.Box, { sx: {
                        width: 80,
                        height: 80,
                        bgcolor: '#ffffff',
                        border: (theme) => `1px solid ${theme.palette.divider}`,
                        borderRadius: 1,
                        display: 'flex',
                        justifyContent: 'center',
                        alignItems: 'center',
                    }, children: status.kind === 'ready' ? ((0,jsx_runtime.jsx)(material_5_1_8_singleton_.Box, { component: "img", src: status.src, alt: "Cluster Thumbnail", sx: { maxWidth: '100%', maxHeight: '100%' } })) : status.kind === 'too-large' ? ((0,jsx_runtime.jsx)(material_5_1_8_singleton_.Typography, { variant: "caption", color: "text.disabled", sx: { textAlign: 'center', px: 1 }, children: "Cluster is too big to show" })) : ((0,jsx_runtime.jsx)(material_5_1_8_singleton_.CircularProgress, { color: "primary" })) }), (0,jsx_runtime.jsxs)(material_5_1_8_singleton_.Box, { sx: { flexGrow: 1 }, children: [(0,jsx_runtime.jsx)(material_5_1_8_singleton_.Typography, { variant: "body2", color: "text.secondary", sx: { width: '100%', textAlign: 'right' }, children: (Math.round(cluster.score * 100) / 100).toFixed(2) }), (0,jsx_runtime.jsx)(material_5_1_8_singleton_.Tooltip, { title: "Size Threshold (Node Score Cutoff)", children: (0,jsx_runtime.jsx)(material_5_1_8_singleton_.Slider, { "aria-label": "Node Score Cutoff", value: cutoff, getAriaValueText: (val) => val.toFixed(2), valueLabelFormat: (val) => val.toFixed(2), step: 0.01, marks: [
                                    {
                                        value: algorithm.getParameters().nodeScoreCutoff,
                                        label: '',
                                    },
                                ], track: false, min: 0, max: 1.0, valueLabelDisplay: "auto", onClick: (event) => event.stopPropagation(), 
                                // select nodes before onChangeCommitted causes another nodes selection asynchronously
                                onChange: handleChange, onChangeCommitted: handleChangeCommitted }) }), (0,jsx_runtime.jsxs)(material_5_1_8_singleton_.Typography, { variant: "body2", color: "text.secondary", children: [cluster.nodes.length, " node", cluster.nodes.length !== 1 ? 's' : ''] })] })] }) }));
});
ClusterPanel.displayName = 'ClusterPanel';
const ExplorePanel = ({ cluster, networkId, }) => {
    const [attributes, setAttributes] = (0,consume_shared_module_default_react_1_8_3_singleton_.useState)([]);
    const [selectedAttribute, setSelectedAttribute] = (0,consume_shared_module_default_react_1_8_3_singleton_.useState)('');
    const [enumerations, setEnumerations] = (0,consume_shared_module_default_react_1_8_3_singleton_.useState)(new Map());
    const tableApi = (0,TableApi.useTableApi)();
    // Get the names of all node-table columns in the network,
    // and set the first one as the default selection if none is selected.
    const updateAttributes = () => {
        let names = [];
        const table = tableApi.getTable(networkId, 'node');
        if (!table.success) {
            console.warn('Failed to read node table columns:', table.error.message);
            setAttributes(names);
            return names;
        }
        names = table.data.columns
            .map((column) => column.name)
            .filter((value, index, self) => self.indexOf(value) === index); // unique names
        names.sort((a, b) => a.toLowerCase().localeCompare(b.toLowerCase()));
        setAttributes(names);
        // set the first attribute as the default selection if none is selected
        if ((!selectedAttribute || selectedAttribute === '') && names.length > 0) {
            setSelectedAttribute(names[0]);
        }
        return names;
    };
    // Count how many times each value of the selected attribute appears across the
    // cluster's nodes. List-valued attributes (e.g. "MCODE::Clusters (n)") count each element.
    const updateEnumerations = () => {
        let counts = new Map();
        if (selectedAttribute && selectedAttribute !== '') {
            for (const nodeId of cluster.nodes) {
                const result = tableApi.getValue(networkId, 'node', nodeId, selectedAttribute);
                if (!result.success)
                    continue;
                const raw = result.data.value;
                if (raw === null || raw === undefined)
                    continue;
                // A list value contributes each of its elements; a scalar contributes once.
                const values = Array.isArray(raw) ? raw : [raw];
                for (const element of values) {
                    if (element === null || element === undefined)
                        continue;
                    // Keep numbers as numbers, everything else as its string form.
                    const key = typeof element === 'number' ? element : String(element);
                    counts.set(key, (counts.get(key) ?? 0) + 1);
                }
                // Sort the map by key ascending (string order for strings, numeric order for numbers).
                counts = new Map([...counts.entries()].sort((a, b) => {
                    if (typeof a[0] === 'number' && typeof b[0] === 'number') {
                        return a[0] - b[0];
                    }
                    return String(a[0]).localeCompare(String(b[0]));
                }));
            }
        }
        setEnumerations(counts);
    };
    (0,consume_shared_module_default_react_1_8_3_singleton_.useEffect)(() => {
        updateAttributes();
    }, [networkId]);
    (0,consume_shared_module_default_react_1_8_3_singleton_.useEffect)(() => {
        updateEnumerations();
    }, [selectedAttribute, cluster, networkId]);
    // The node table of this network changed. 'data:changed' can't tell a column
    // schema change from a row-value change (creating a column in the Cytoscape
    // Web UI writes default values, so rowIds is non-empty either way), so refresh
    // both the attribute list and the enumerations.
    (0,EventBus.useCyWebEvent)('data:changed', ({ networkId: changedNetworkId, tableType }) => {
        if (tableType !== 'node' || changedNetworkId !== networkId)
            return;
        // Check whether the selected attribute's column was removed
        let stillExists = true;
        if (selectedAttribute && selectedAttribute !== '') {
            const table = tableApi.getTable(networkId, 'node');
            stillExists = table.success && table.data.columns.some((column) => column.name === selectedAttribute);
        }
        const newAttributes = updateAttributes();
        // If the selected attribute was removed, select the first attribute in the new list (or empty string if none).
        if (!stillExists)
            setSelectedAttribute(newAttributes.length > 0 ? newAttributes[0] : '');
        updateEnumerations();
    });
    const handleOnChange = (event) => {
        setSelectedAttribute(event.target.value);
    };
    return ((0,jsx_runtime.jsxs)(material_5_1_8_singleton_.Box, { children: [(0,jsx_runtime.jsxs)(material_5_1_8_singleton_.Box, { sx: {
                    display: 'flex',
                    alignItems: 'center',
                    p: 1,
                    gap: 1,
                }, children: [(0,jsx_runtime.jsx)(material_5_1_8_singleton_.Typography, { variant: "body1", children: "Node Attribute:" }), (0,jsx_runtime.jsx)(material_5_1_8_singleton_.Select, { value: selectedAttribute, disabled: attributes.length === 0, size: "small", displayEmpty: true, renderValue: () => !selectedAttribute || selectedAttribute === '' ? '-- Select an attribute --' : selectedAttribute, onChange: handleOnChange, sx: {
                            flexGrow: 1,
                            minWidth: 120,
                        }, children: attributes.map((attr) => ((0,jsx_runtime.jsx)(material_5_1_8_singleton_.MenuItem, { value: attr, children: attr }, attr))) })] }), (0,jsx_runtime.jsx)(material_5_1_8_singleton_.TableContainer, { sx: {
                    maxHeight: 240,
                    border: (theme) => `1px solid ${theme.palette.divider}`,
                    borderRadius: 1,
                }, children: (0,jsx_runtime.jsxs)(material_5_1_8_singleton_.Table, { stickyHeader: true, size: "small", children: [(0,jsx_runtime.jsx)(material_5_1_8_singleton_.TableHead, { children: (0,jsx_runtime.jsxs)(material_5_1_8_singleton_.TableRow, { children: [(0,jsx_runtime.jsx)(material_5_1_8_singleton_.TableCell, { align: "left", children: "Value" }, "value"), (0,jsx_runtime.jsx)(material_5_1_8_singleton_.TableCell, { align: "left", width: 120, sx: { borderLeft: (theme) => `1px solid ${theme.palette.divider}` }, children: "Occurrence" }, "occurrence")] }) }), (0,jsx_runtime.jsx)(material_5_1_8_singleton_.TableBody, { children: Array.from(enumerations.entries()).map(([val, count], idx) => ((0,jsx_runtime.jsxs)(material_5_1_8_singleton_.TableRow, { children: [(0,jsx_runtime.jsx)(material_5_1_8_singleton_.TableCell, { align: typeof val === 'number' ? 'right' : 'left', children: val }), (0,jsx_runtime.jsx)(material_5_1_8_singleton_.TableCell, { align: "right", sx: { borderLeft: (theme) => `1px solid ${theme.palette.divider}` }, children: count })] }, `${cluster.rank}-${selectedAttribute}-${val}`))) })] }) })] }));
};
const MCODEPanel = () => {
    const workspaceApi = (0,WorkspaceApi.useWorkspaceApi)();
    const elementApi = (0,ElementApi.useElementApi)();
    const selectionApi = (0,SelectionApi.useSelectionApi)();
    const tableApi = (0,TableApi.useTableApi)();
    const [currentNetworkId, setCurrentNetworkId] = (0,consume_shared_module_default_react_1_8_3_singleton_.useState)(() => {
        const current = workspaceApi.getCurrentNetworkId();
        return current.success ? current.data.networkId : null;
    });
    const [results, setResults] = (0,consume_shared_module_default_react_1_8_3_singleton_.useState)([]);
    const [selectedResult, setSelectedResult] = (0,consume_shared_module_default_react_1_8_3_singleton_.useState)(null);
    const [showParametersResult, setShowParametersResult] = (0,consume_shared_module_default_react_1_8_3_singleton_.useState)(false);
    const [selectedCluster, setSelectedCluster] = (0,consume_shared_module_default_react_1_8_3_singleton_.useState)(null);
    const [analysisDialogOpen, setAnalysisDialogOpen] = (0,consume_shared_module_default_react_1_8_3_singleton_.useState)(false);
    const [noResultsOpen, setNoResultsOpen] = (0,consume_shared_module_default_react_1_8_3_singleton_.useState)(false);
    // The "Analyzing network…" state is shown while the MCODE worker is running.
    // It can be cancelled by the user, which aborts the worker and sets a flag
    // that the main thread checks at a yield point after the worker finishes.
    const [analyzing, setAnalyzing] = (0,consume_shared_module_default_react_1_8_3_singleton_.useState)(false);
    // Post-worker phase: committing the result + writing node columns.
    // Shown as a separate, non-cancellable "Saving results…" state
    // (the worker is done, so there's nothing left to cancel).
    const [saving, setSaving] = (0,consume_shared_module_default_react_1_8_3_singleton_.useState)(false);
    // Monotonically increasing result id.
    // It never reuses an id, even after results are discarded,
    // so a new result can't collide with a deleted one's leftover node columns.
    const nextResultId = (0,consume_shared_module_default_react_1_8_3_singleton_.useRef)(1);
    // Set by the Cancel button. Covers the whole submit operation, not just the
    // worker: the worker is aborted via cancelMcode(), but the post-worker
    // main-thread work (writing node columns, committing the result) is only
    // cancellable by checking this flag at a yield point — see handleSubmitAnalysis.
    const analysisCancelled = (0,consume_shared_module_default_react_1_8_3_singleton_.useRef)(false);
    // Runs the MCODE algorithm in a web worker so the UI thread stays responsive.
    const { run: runMcode, cancel: cancelMcode } = useMcodeWorker();
    // Cache of every network's edges ({id, source, target}), so cluster thumbnails
    // filter an in-memory list instead of each one re-fetching all edges from the
    // source network. Keyed by network id, so results on the same network share it.
    const networkEdgesCache = (0,consume_shared_module_default_react_1_8_3_singleton_.useRef)(new Map());
    const getNetworkEdges = (networkId) => {
        const cached = networkEdgesCache.current.get(networkId);
        if (cached)
            return cached;
        const result = [];
        const idsResult = elementApi.getEdgeIds(networkId);
        if (idsResult.success) {
            for (const edgeId of idsResult.data.edgeIds) {
                const edge = elementApi.getEdge(networkId, edgeId);
                if (!edge.success)
                    continue;
                result.push({ id: edgeId, source: edge.data.sourceId, target: edge.data.targetId });
            }
        }
        networkEdgesCache.current.set(networkId, result);
        return result;
    };
    // The selected result's source-network edges, fetched once per network.
    const networkEdges = (0,consume_shared_module_default_react_1_8_3_singleton_.useMemo)(() => (selectedResult ? getNetworkEdges(selectedResult.networkId) : []), 
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [selectedResult?.networkId]);
    (0,EventBus.useCyWebEvent)('network:switched', ({ networkId: newId, previousId }) => {
        console.debug(`current network changed: ${previousId || '(none)'} → ${newId}`);
        setCurrentNetworkId(newId);
    });
    (0,EventBus.useCyWebEvent)('network:deleted', ({ networkId }) => {
        console.debug(`Network deleted: ${networkId}`);
        // Delete all MCODE results that have the same networkId, and clear the selected result if it's among them.
        setResults((prev) => {
            const filtered = prev.filter((r) => r.networkId !== networkId);
            if (selectedResult && selectedResult.networkId === networkId) {
                setSelectedResult(null);
                setSelectedCluster(null);
            }
            return filtered;
        });
    });
    const handleNewAnalysisClick = () => {
        setAnalysisDialogOpen(true);
    };
    const handleSubmitAnalysis = async (parameters) => {
        if (!currentNetworkId) {
            return;
        }
        // 1. Determine the set of nodes to analyze. For SELECTION scope, restrict
        //    to the currently selected nodes; otherwise use the whole network.
        let nodeIds;
        if (parameters.scope === 'SELECTION') {
            const selection = selectionApi.getSelection(currentNetworkId);
            if (!selection.success) {
                console.warn('Failed to read selection:', selection.error.message);
                return;
            }
            nodeIds = selection.data.selectedNodes;
        }
        else {
            const nodesResult = elementApi.getNodeIds(currentNetworkId);
            if (!nodesResult.success) {
                console.warn('Failed to read nodes:', nodesResult.error.message);
                return;
            }
            nodeIds = nodesResult.data.nodeIds;
        }
        // 2. Read the network's graph via ElementApi as an undirected
        //    adjacency map { nodeId -> neighborNodeIds[] } for MCODE. When the
        //    scope is a selection, keep only neighbors that are themselves in scope.
        const inScope = new Set(nodeIds);
        const adjacency = new Map();
        for (const nodeId of nodeIds) {
            const neighbors = elementApi.getConnectedNodes(currentNetworkId, nodeId);
            const neighborIds = neighbors.success ? neighbors.data.nodeIds : [];
            adjacency.set(nodeId, parameters.scope === 'SELECTION'
                ? neighborIds.filter((id) => inScope.has(id))
                : neighborIds);
        }
        console.debug('Adjacency map:', adjacency);
        // 3. Run MCODE in a web worker so a large network doesn't freeze the UI.
        //    A spinner is shown while `analyzing` is true. The spinner stays up for
        //    the *whole* operation (worker + committing the result), so it's cleared
        //    once at the end in `finally`.
        analysisCancelled.current = false;
        let clusters;
        let algorithm;
        setAnalyzing(true);
        try {
            try {
                ;
                ({ clusters, algorithm } = await runMcode(adjacency, parameters));
            }
            catch (err) {
                // A user cancellation is expected; only warn on genuine failures.
                if (err instanceof McodeCancelledError) {
                    console.debug('MCODE analysis cancelled');
                }
                else {
                    console.warn('MCODE analysis failed:', err);
                }
                return;
            }
            // If nothing was found, don't add an empty result; just inform the user.
            if (clusters.length === 0) {
                setNoResultsOpen(true);
                return;
            }
            // The worker is done, but committing the result still does heavy,
            // un-interruptible main-thread work (writing 3 node columns across every
            // node, then rendering the cluster thumbnails). Yield once so a Cancel
            // click queued during the run is delivered, then honor it — otherwise the
            // spinner would sit through that work with nothing left to cancel.
            await new Promise((resolve) => setTimeout(resolve));
            if (analysisCancelled.current) {
                console.debug('MCODE analysis cancelled');
                return;
            }
            // The worker is done — switch to the non-cancellable "Saving results…"
            // phase and let it paint before the heavy synchronous work below.
            setAnalyzing(false);
            setSaving(true);
            await new Promise((resolve) => setTimeout(resolve));
            // 4. Build the result. The name is "{COUNT} - {network name}" where COUNT
            //    is the new result's position in the results array (1-based, i.e. the
            //    last index once it is appended).
            const summary = workspaceApi.getNetworkSummary(currentNetworkId);
            const networkName = summary.success ? summary.data.name : currentNetworkId;
            const id = nextResultId.current;
            nextResultId.current += 1;
            const newResult = {
                id,
                name: `${id} - ${networkName}`,
                networkId: currentNetworkId,
                algorithm,
                clusters,
            };
            setResults((prev) => [...prev, newResult]);
            setSelectedResult(newResult);
            setSelectedCluster(null);
            console.debug(`MCODE found ${clusters.length} cluster(s)`, clusters);
            // 5. Add the MCODE result columns to the source network's node table:
            //    "MCODE::Score (n)", "MCODE::Node Status (n)", "MCODE::Clusters (n)".
            const { columns, rows } = buildMcodeNodeTableData(id, clusters, algorithm.getScores());
            for (const col of columns) {
                const created = tableApi.createColumn(currentNetworkId, 'node', col.name, col.type, col.defaultValue);
                if (!created.success) {
                    console.warn(`Failed to create node column "${col.name}":`, created.error.message);
                }
            }
            console.debug('Writing MCODE node column values...', rows);
            const cellEdits = Object.entries(rows).flatMap(([nodeId, values]) => Object.entries(values).map(([column, value]) => ({ id: nodeId, column, value })));
            const edited = tableApi.setValues(currentNetworkId, 'node', cellEdits);
            console.debug('Finished writing MCODE node column values--Success:', edited.success);
            if (!edited.success) {
                console.warn('Failed to write MCODE node column values:', edited.error.message);
            }
        }
        finally {
            setAnalyzing(false);
            setSaving(false);
        }
    };
    // Cancel the whole analysis: abort the worker if it's still running, and flag
    // the operation so the post-worker commit step (if the worker already
    // finished) is skipped at its yield checkpoint.
    const handleCancelAnalysis = () => {
        analysisCancelled.current = true;
        cancelMcode();
    };
    const handleClusterClick = (0,consume_shared_module_default_react_1_8_3_singleton_.useCallback)((cluster) => {
        if (selectedCluster === cluster) {
            return; // already selected, do nothing
        }
        setSelectedCluster(cluster);
        // Re-select the nodes in the source network so the selection tracks the newly selected cluster.
        if (selectedResult) {
            const selected = selectionApi.exclusiveSelect(selectedResult.networkId, cluster.nodes, []);
            if (!selected.success) {
                console.warn('Failed to select cluster nodes:', selected.error.message);
            }
        }
    }, [selectedResult, selectedCluster, selectionApi]);
    const handleExploreCluster = (0,consume_shared_module_default_react_1_8_3_singleton_.useCallback)((cluster, nodeScoreCutoff) => {
        setSelectedCluster(cluster);
        // Re-select the now changed nodes in the source network so the selection tracks the new cluster.
        if (selectedResult) {
            const selected = selectionApi.exclusiveSelect(selectedResult.networkId, cluster.nodes, []);
            if (!selected.success) {
                console.warn('Failed to re-select explored cluster nodes:', selected.error.message);
            }
        }
    }, [selectedResult, selectedCluster, selectionApi]);
    const handleShowAnalysisParameters = (show) => {
        setShowParametersResult(show);
    };
    // Remove the result's MCODE node-table columns from its source network.
    const removeResultColumns = (result) => {
        for (const name of mcodeColumnNames(result.id)) {
            console.debug(`Deleting column "${name}" from network ${result.networkId}...`);
            const res = tableApi.deleteColumn(result.networkId, 'node', name);
            if (!res.success) {
                console.warn(`Failed to delete node column "${name}":`, res.error.message);
            }
        }
    };
    const handleDiscardSelectedResult = () => {
        if (selectedResult) {
            removeResultColumns(selectedResult);
            setSelectedResult((prev) => {
                const index = results.indexOf(prev);
                if (index > 0) {
                    return results[index - 1];
                }
                return results.length > 1 ? results[1] : null;
            });
            const updatedResults = results.filter((r) => r !== selectedResult);
            setResults(updatedResults);
            setSelectedCluster(null);
            if (updatedResults.length === 0) {
                nextResultId.current = 1;
            }
        }
    };
    const handleDiscardAllResults = () => {
        results.forEach(removeResultColumns);
        setSelectedResult(null);
        setResults([]);
        setSelectedCluster(null);
        nextResultId.current = 1;
    };
    return ((0,jsx_runtime.jsxs)(jsx_runtime.Fragment, { children: [(0,jsx_runtime.jsxs)(material_5_1_8_singleton_.Box, { sx: {
                    height: '100%',
                    display: 'flex',
                    flexDirection: 'column',
                }, children: [(0,jsx_runtime.jsxs)(material_5_1_8_singleton_.Box, { sx: {
                            display: 'flex',
                            alignItems: 'center',
                            backgroundColor: 'background.default',
                            p: 1,
                            gap: 1,
                        }, children: [(0,jsx_runtime.jsx)(material_5_1_8_singleton_.Select, { value: selectedResult?.name || '', disabled: results.length === 0, size: "small", onChange: (e) => {
                                    const result = results.find((r) => r.name === e.target.value) || null;
                                    setSelectedResult(result);
                                    setSelectedCluster(null);
                                }, displayEmpty: true, renderValue: (value) => {
                                    if (!value) {
                                        return ((0,jsx_runtime.jsx)(material_5_1_8_singleton_.Typography, { color: results.length > 0 ? 'text.secondary' : 'text.disabled', children: results.length > 0 ? '-- Select Result --' : '-- No Results --' }));
                                    }
                                    return (0,jsx_runtime.jsx)(jsx_runtime.Fragment, { children: value });
                                }, sx: {
                                    flexGrow: 1,
                                    minWidth: 200,
                                    bgcolor: results.length === 0 ? 'transparent' : 'background.paper',
                                }, children: results.map((result) => ((0,jsx_runtime.jsx)(material_5_1_8_singleton_.MenuItem, { value: result.name, children: result.name }, result.name))) }), (0,jsx_runtime.jsx)(material_5_1_8_singleton_.Tooltip, { title: "New analysis...", children: (0,jsx_runtime.jsx)("span", { children: (0,jsx_runtime.jsx)(material_5_1_8_singleton_.Button, { variant: "contained", disabled: !currentNetworkId || analyzing || saving, onClick: handleNewAnalysisClick, sx: {
                                            minWidth: 24,
                                            px: 1,
                                        }, children: (0,jsx_runtime.jsx)(Add/* default */.A, {}) }) }) }), (0,jsx_runtime.jsx)(OptionsMenu, { currentNetworkId: currentNetworkId, results: results, selectedResult: selectedResult, selectedCluster: selectedCluster, onShowAnalysisParameters: handleShowAnalysisParameters, onDiscardSelectedResult: handleDiscardSelectedResult, onDiscardAllResults: handleDiscardAllResults })] }), showParametersResult && selectedResult && ((0,jsx_runtime.jsxs)(material_5_1_8_singleton_.Box, { sx: {
                            p: 2,
                            backgroundColor: 'background.default',
                            borderTop: (theme) => `2px solid ${theme.palette.background.paper}`,
                        }, children: [(0,jsx_runtime.jsxs)(material_5_1_8_singleton_.Typography, { variant: "body2", color: "text.secondary", children: ["Scope: ", selectedResult.algorithm.getParameters().scope === 'NETWORK' ? 'Whole Network' : 'Selected Nodes'] }), (0,jsx_runtime.jsxs)(material_5_1_8_singleton_.Typography, { variant: "body2", color: "text.secondary", children: ["Include Loops: ", selectedResult.algorithm.getParameters().includeLoops ? 'Yes' : 'No'] }), (0,jsx_runtime.jsxs)(material_5_1_8_singleton_.Typography, { variant: "body2", color: "text.secondary", children: ["Degree Cutoff: ", selectedResult.algorithm.getParameters().degreeCutoff] }), (0,jsx_runtime.jsxs)(material_5_1_8_singleton_.Typography, { variant: "body2", color: "text.secondary", children: ["Haircut: ", selectedResult.algorithm.getParameters().haircut ? 'Yes' : 'No'] }), (0,jsx_runtime.jsxs)(material_5_1_8_singleton_.Typography, { variant: "body2", color: "text.secondary", children: ["Fluff: ", selectedResult.algorithm.getParameters().fluff ? 'Yes' : 'No'] }), selectedResult.algorithm.getParameters().fluff && ((0,jsx_runtime.jsxs)(material_5_1_8_singleton_.Typography, { variant: "body2", color: "text.secondary", children: ["Fluff Node Density Cutoff: ", selectedResult.algorithm.getParameters().fluffNodeDensityCutoff] })), (0,jsx_runtime.jsxs)(material_5_1_8_singleton_.Typography, { variant: "body2", color: "text.secondary", children: ["Node Score Cutoff: ", selectedResult.algorithm.getParameters().nodeScoreCutoff] }), (0,jsx_runtime.jsxs)(material_5_1_8_singleton_.Typography, { variant: "body2", color: "text.secondary", children: ["K-Core: ", selectedResult.algorithm.getParameters().kCore] }), (0,jsx_runtime.jsxs)(material_5_1_8_singleton_.Typography, { variant: "body2", color: "text.secondary", children: ["Max Depth: ", selectedResult.algorithm.getParameters().maxDepthFromStart] })] })), (0,jsx_runtime.jsx)(material_5_1_8_singleton_.Box, { sx: {
                            flexGrow: 1,
                            overflowY: 'auto',
                        }, children: selectedResult?.clusters.map((cluster) => (
                        // Key by result + seed so switching results remounts the panels
                        // (their uncontrolled size Slider would otherwise keep a stale
                        // value from the same list position in the previous result). The key
                        // stays stable across exploration, since the seed id is preserved.
                        (0,jsx_runtime.jsx)(ClusterPanel, { cluster: cluster, edges: networkEdges, algorithm: selectedResult.algorithm, selected: selectedCluster === cluster, onClick: handleClusterClick, onExplore: handleExploreCluster }, `${selectedResult.id}-${cluster.rank}`))) }), selectedResult && selectedCluster && ((0,jsx_runtime.jsxs)(material_5_1_8_singleton_.Accordion, { "data-testid": "layout-tools-accordion", sx: {
                            backgroundImage: 'none',
                            boxShadow: 'none',
                        }, children: [(0,jsx_runtime.jsx)(material_5_1_8_singleton_.AccordionSummary, { expandIcon: (0,jsx_runtime.jsx)(ExpandLess/* default */.A, {}), "aria-controls": "manual-layout", sx: {
                                    minHeight: '40px', // collapsed summary height
                                    '&.Mui-expanded': {
                                        minHeight: '40px', // expanded summary height
                                        borderTop: (theme) => `1px solid ${theme.palette.divider}`,
                                    },
                                    '.MuiAccordionSummary-content': {
                                        marginTop: '12px !important',
                                    },
                                    '& .MuiAccordionSummary-expandIconWrapper': {
                                        color: (theme) => theme.palette.text.secondary,
                                    },
                                }, children: (0,jsx_runtime.jsxs)(material_5_1_8_singleton_.Typography, { children: ["Explore: Cluster ", selectedCluster.rank] }) }), (0,jsx_runtime.jsx)(material_5_1_8_singleton_.AccordionDetails, { children: (0,jsx_runtime.jsx)(ExplorePanel, { cluster: selectedCluster, networkId: selectedResult.networkId }) })] }))] }), currentNetworkId && ((0,jsx_runtime.jsx)(NewAnalysisDialog, { networkId: currentNetworkId, open: analysisDialogOpen, onClose: () => setAnalysisDialogOpen(false), onSubmit: handleSubmitAnalysis })), (0,jsx_runtime.jsxs)(material_5_1_8_singleton_.Dialog, { open: analyzing || saving, children: [(0,jsx_runtime.jsxs)(material_5_1_8_singleton_.DialogContent, { sx: { display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }, children: [(0,jsx_runtime.jsx)(material_5_1_8_singleton_.CircularProgress, { color: "primary" }), (0,jsx_runtime.jsx)(material_5_1_8_singleton_.Typography, { children: saving ? 'Saving results…' : 'Analyzing network…' })] }), analyzing && ((0,jsx_runtime.jsx)(material_5_1_8_singleton_.DialogActions, { children: (0,jsx_runtime.jsx)(material_5_1_8_singleton_.Button, { variant: "outlined", color: "error", onClick: handleCancelAnalysis, children: "Cancel" }) }))] }), (0,jsx_runtime.jsxs)(material_5_1_8_singleton_.Dialog, { open: noResultsOpen, onClose: () => setNoResultsOpen(false), children: [(0,jsx_runtime.jsx)(material_5_1_8_singleton_.DialogTitle, { children: "No Results" }), (0,jsx_runtime.jsx)(material_5_1_8_singleton_.DialogContent, { children: (0,jsx_runtime.jsx)(material_5_1_8_singleton_.DialogContentText, { sx: { whiteSpace: 'pre-line' }, children: 'No clusters were found.\n'
                                + 'You can try changing the MCODE parameters or\n'
                                + 'modifying your node selection if you are using\n'
                                + 'a selection-specific scope.' }) }), (0,jsx_runtime.jsx)(material_5_1_8_singleton_.DialogActions, { children: (0,jsx_runtime.jsx)(material_5_1_8_singleton_.Button, { onClick: () => setNoResultsOpen(false), variant: "contained", children: "OK" }) })] })] }));
};
/* harmony default export */ const components_MCODEPanel = (MCODEPanel);


/***/ }

};

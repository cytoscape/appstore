/******/ var __webpack_modules__ = ({

/***/ 8823
() {


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
const MCODE_ANALYSIS_SCOPE_LABELS = (/* unused pure expression or super */ null && ({
    NETWORK: 'In Whole Network',
    SELECTION: 'From Selection',
}));
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

;// ./src/model/mcode.worker.ts
/**
 * Web worker entry point for MCODE analysis.
 *
 * Receives an adjacency map + parameters from the main thread, runs the
 * (potentially long, synchronous) MCODE algorithm here so the UI thread is
 * never blocked, and posts the ranked clusters back.
 *
 * Bundled automatically by webpack 5 via the `new Worker(new URL(...))` call
 * in `useMcodeWorker`. Its import graph (mcodeAlgorithm → mcodeGraph →
 * mcodeTypes) is pure and free of React / MUI / cyweb dependencies.
 */

// `self` is the DedicatedWorkerGlobalScope. We cast to a minimal typed shape so
// this file does not need the (DOM-conflicting) "webworker" TS lib enabled.
const ctx = self;
ctx.onmessage = (event) => {
    const { adjacency, parameters } = event.data;
    try {
        const alg = new MCODEAlgorithm(parameters);
        const clusters = alg.run(adjacency);
        // Send a snapshot of the scored state so the main thread can rehydrate the
        // algorithm (cached nodeInfo/scores) without rescoring.
        ctx.postMessage({ type: 'success', clusters, snapshot: alg.toSnapshot() });
    }
    catch (err) {
        ctx.postMessage({
            type: 'error',
            message: err instanceof Error ? err.message : String(err),
        });
    }
};


/***/ }

/******/ });
/************************************************************************/
/******/ // The module cache
/******/ var __webpack_module_cache__ = {};
/******/ 
/******/ // The require function
/******/ function __webpack_require__(moduleId) {
/******/ 	// Check if module is in cache
/******/ 	var cachedModule = __webpack_module_cache__[moduleId];
/******/ 	if (cachedModule !== undefined) {
/******/ 		return cachedModule.exports;
/******/ 	}
/******/ 	// Create a new module (and put it into the cache)
/******/ 	var module = __webpack_module_cache__[moduleId] = {
/******/ 		// no module.id needed
/******/ 		// no module.loaded needed
/******/ 		exports: {}
/******/ 	};
/******/ 
/******/ 	// Execute the module function
/******/ 	var execOptions = { id: moduleId, module: module, factory: __webpack_modules__[moduleId], require: __webpack_require__ };
/******/ 	__webpack_require__.i.forEach(function(handler) { handler(execOptions); });
/******/ 	module = execOptions.module;
/******/ 	execOptions.factory.call(module.exports, module, module.exports, execOptions.require);
/******/ 
/******/ 	// Return the exports of the module
/******/ 	return module.exports;
/******/ }
/******/ 
/******/ // expose the modules object (__webpack_modules__)
/******/ __webpack_require__.m = __webpack_modules__;
/******/ 
/******/ // expose the module cache
/******/ __webpack_require__.c = __webpack_module_cache__;
/******/ 
/******/ // expose the module execution interceptor
/******/ __webpack_require__.i = [];
/******/ 
/******/ // the startup function
/******/ __webpack_require__.x = x => {};
/************************************************************************/
/******/ /* webpack/runtime/federation runtime */
/******/ (() => {
/******/ 	if(!__webpack_require__.federation){
/******/ 		__webpack_require__.federation = {
/******/ 			initOptions: {"name":"mcode","remotes":[],"shareStrategy":"version-first"},
/******/ 			chunkMatcher: function(chunkId) {return false},
/******/ 			rootOutputDir: "",
/******/ 			bundlerRuntimeOptions: { remotes: { remoteInfos: {"cyweb":[{"alias":"cyweb","name":"","entry":"","shareScope":"default","externalType":"unknown"}]}, webpackRequire: __webpack_require__,idToRemoteMap: {}, chunkMapping: {},idToExternalAndNameMapping: {} } }
/******/ 		};
/******/ 	__webpack_require__.consumesLoadingData = {}
/******/ 	__webpack_require__.remotesLoadingData = {}
/******/ 	}
/******/ })();
/******/ 
/******/ /* webpack/runtime/compat get default export */
/******/ (() => {
/******/ 	// getDefaultExport function for compatibility with non-harmony modules
/******/ 	__webpack_require__.n = (module) => {
/******/ 		var getter = module && module.__esModule ?
/******/ 			() => (module['default']) :
/******/ 			() => (module);
/******/ 		__webpack_require__.d(getter, { a: getter });
/******/ 		return getter;
/******/ 	};
/******/ })();
/******/ 
/******/ /* webpack/runtime/define property getters */
/******/ (() => {
/******/ 	// define getter functions for harmony exports
/******/ 	__webpack_require__.d = (exports, definition) => {
/******/ 		for(var key in definition) {
/******/ 			if(__webpack_require__.o(definition, key) && !__webpack_require__.o(exports, key)) {
/******/ 				Object.defineProperty(exports, key, { enumerable: true, get: definition[key] });
/******/ 			}
/******/ 		}
/******/ 	};
/******/ })();
/******/ 
/******/ /* webpack/runtime/hasOwnProperty shorthand */
/******/ (() => {
/******/ 	__webpack_require__.o = (obj, prop) => (Object.prototype.hasOwnProperty.call(obj, prop))
/******/ })();
/******/ 
/******/ /* webpack/runtime/sharing */
/******/ (() => {
/******/ 	__webpack_require__.S = {};
/******/ 	var initPromises = {};
/******/ 	var initTokens = {};
/******/ 	__webpack_require__.I = (name, initScope) => {
/******/ 		if(!initScope) initScope = [];
/******/ 		// handling circular init calls
/******/ 		var initToken = initTokens[name];
/******/ 		if(!initToken) initToken = initTokens[name] = {};
/******/ 		if(initScope.indexOf(initToken) >= 0) return;
/******/ 		initScope.push(initToken);
/******/ 		// only runs once
/******/ 		if(initPromises[name]) return initPromises[name];
/******/ 		// creates a new share scope if needed
/******/ 		if(!__webpack_require__.o(__webpack_require__.S, name)) __webpack_require__.S[name] = {};
/******/ 		// runs all init snippets from all modules reachable
/******/ 		var scope = __webpack_require__.S[name];
/******/ 		var warn = (msg) => {
/******/ 			if (typeof console !== "undefined" && console.warn) console.warn(msg);
/******/ 		};
/******/ 		var uniqueName = "@cytoscape-web/";
/******/ 		var register = (name, version, factory, eager) => {
/******/ 			var versions = scope[name] = scope[name] || {};
/******/ 			var activeVersion = versions[version];
/******/ 			if(!activeVersion || (!activeVersion.loaded && (!eager != !activeVersion.eager ? eager : uniqueName > activeVersion.from))) versions[version] = { get: factory, from: uniqueName, eager: !!eager };
/******/ 		};
/******/ 		var initExternal = (id) => {
/******/ 			var handleError = (err) => (warn("Initialization of sharing external failed: " + err));
/******/ 			try {
/******/ 				var module = __webpack_require__(id);
/******/ 				if(!module) return;
/******/ 				var initFn = (module) => (module && module.init && module.init(__webpack_require__.S[name], initScope))
/******/ 				if(module.then) return promises.push(module.then(initFn, handleError));
/******/ 				var initResult = initFn(module);
/******/ 				if(initResult && initResult.then) return promises.push(initResult['catch'](handleError));
/******/ 			} catch(err) { handleError(err); }
/******/ 		}
/******/ 		var promises = [];
/******/ 		switch(name) {
/******/ 		}
/******/ 		if(!promises.length) return initPromises[name] = 1;
/******/ 		return initPromises[name] = Promise.all(promises).then(() => (initPromises[name] = 1));
/******/ 	};
/******/ })();
/******/ 
/******/ /* webpack/runtime/sharing */
/******/ (() => {
/******/ 	__webpack_require__.federation.initOptions.shared = {}
/******/ 	__webpack_require__.S = {};
/******/ 	var initPromises = {};
/******/ 	var initTokens = {};
/******/ 	__webpack_require__.I = (name, initScope) => {
/******/ 		return __webpack_require__.federation.bundlerRuntime.I({	shareScopeName: name,
/******/ 			webpackRequire: __webpack_require__,
/******/ 			initPromises: initPromises,
/******/ 			initTokens: initTokens,
/******/ 			initScope: initScope,
/******/ 		})
/******/ 	};
/******/ })();
/******/ 
/************************************************************************/
/******/ // run runtime startup
/******/ __webpack_require__.x();
/******/ // module cache are used so entry inlining is disabled
/******/ // startup
/******/ // Load entry module and return exports
/******/ var __webpack_exports__ = __webpack_require__(8823);
/******/ 

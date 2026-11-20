// IR arrays are immutable during graph projection; keep indexes scoped to their lifetime.
const callableIndexes = new WeakMap();
const referenceIndexes = new WeakMap();
const rangeStartCompare = (a, b) => pointCompare(a.start, b.start);
const buildRangeIndex = (values, getRange) => {
    const rows = values.flatMap((value, index) => {
        const range = getRange(value);
        return range === null ? [] : [{ value, index, range }];
    }).sort((a, b) => rangeStartCompare(a.range, b.range) || a.index - b.index);
    const build = (lo, hi) => {
        if (lo >= hi) return null;
        const mid = (lo + hi) >>> 1;
        const row = rows[mid], left = build(lo, mid), right = build(mid + 1, hi);
        const starts = [row.range.start, left?.minStart, right?.minStart].filter(Boolean);
        const ends = [row.range.end, left?.maxEnd, right?.maxEnd].filter(Boolean);
        const minEnds = [row.range.end, left?.minEnd, right?.minEnd].filter(Boolean);
        return { row, left, right,
            minStart: starts.reduce((a,b) => pointCompare(a,b) <= 0 ? a : b),
            maxStart: right?.maxStart ?? row.range.start,
            minEnd: minEnds.reduce((a,b) => pointCompare(a,b) <= 0 ? a : b),
            maxEnd: ends.reduce((a,b) => pointCompare(a,b) >= 0 ? a : b) };
    };
    return { length: values.length, root: build(0, rows.length) };
};
const indexedRanges = (cache, values, getRange) => {
    let index = cache.get(values);
    if (index === undefined || index.length !== values.length) {
        index = buildRangeIndex(values, getRange);
        cache.set(values, index);
    }
    return index.root;
};
const queryRanges = (tree, range, containing, result) => {
    if (tree === null) return;
    if (containing
        ? pointCompare(tree.minStart, range.start) > 0 || pointCompare(tree.maxEnd, range.end) < 0
        : pointCompare(tree.maxStart, range.start) < 0 || pointCompare(tree.minEnd, range.end) > 0)
        return;
    if (containing ? contains(tree.row.range, range) : contains(range, tree.row.range))
        result.push(tree.row);
    queryRanges(tree.left, range, containing, result);
    queryRanges(tree.right, range, containing, result);
};
/** Find the same innermost retained callable without scanning all callables per binding. */
export const owningSemanticCallableNode = (location, ir, nodes) => {
    if (location === null) return undefined;
    const candidates = [];
    queryRanges(indexedRanges(callableIndexes, ir.callables, value => value.location), location, true, candidates);
    candidates.sort((a,b) => compareCodePoints(positionKey(b.range), positionKey(a.range)) || a.index - b.index);
    for (const {value} of candidates) {
        const node = nodes.get(value.callableId);
        if (node !== undefined) return node;
    }
    return undefined;
};
/** Preserve input order while looking up references inside one exact source range. */
export const semanticNodesWithinRange = (nodes, range) => {
    const candidates = [];
    queryRanges(indexedRanges(referenceIndexes, nodes, value => value.identity.source_range), range, false, candidates);
    return candidates.sort((a,b) => a.index - b.index).map(row => row.value);
};

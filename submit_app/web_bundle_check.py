import zipfile
from zipfile import ZipFile
from dataclasses import dataclass
from pathlib import Path
#remoteEntry.js exists (probably redundant)

#./AppConfig load test

#CyApp.id, manifest id, and Module Federation scope match

#React, ReactDOM, and MUI shared dependency compatibility

#compatibleHostVersion is valid semver

#@cytoscape-web/api-types availability and version report

#Public App API usage scan

#Deprecated raw store expose usage scan

#Bundle size report and large-increase warning

#Dependency vulnerability scan

#License report

"""
Detection/reporting for:
eval() or Function()
direct innerHTML assignment
document.cookie
localStorage or sessionStorage
new fetch() or XMLHttpRequest domains"""

PUBLIC_API_SPECIFIERS = [
    "@cytoscape-web/PLACEHOLDER-API"
]

BUNDLE_SIZE_WARNING_THRESHOLD = 0.5 #50% growth in bundle size warrants a warning

JS_EXTENSIONS = ['.js', 'mjs']


@dataclass
class checkResult:
    name: str
    status: str # "pass" | "fail" | "warning" | "not_applicable"
    summary: str
    details: dict = field(default_factory=dict)

    def to_dict(self):
        return {
            'name': self.name,
            'status': self.status,
            'summary': self.summary,
            'details': self.details
        }
    
def _unpack_zip(bundle_path: str, dest: Path):
    with zipfile.ZipFile(bundle_path) as zf:
        zf.extractall(dest)

def _iter_js(root: Path):
    for path in root.rglob("*"):
        if path.is_file() and path.suffix in JS_EXTENSIONS:
            yield path
            
def _find_files_with_pattern(files, pattern: re.Pattern, context_chars: int = 40):
    matches = []

    for path in files:
        try:
            text = path.read_text(encoding='utf-8', errors='ignore'):
        except OSError:
            continue
        
        for m in pattern.finditer(text):
            start = max(0, m.start() - context_chars)
            end = min(len(text), m.end() + context_chars)
            matches.append({
                'file': str(path),
                'match': m.group(0),
                'context': text[start:end]
            })

    return matches


#----------Checks begin here----------------

def check_bundle_size(bundle_path: str, prev_size_bytes) -> CheckResult:
    size = Path(bundle_path).stat().st_size
    details = {"size_bytes": size}

    if prev_size_bytes is None:
        return CheckResult(
            name="bundle_size",
            status="pass",
            summary=f"Bundle size: {size:,} bytes (no previous release to compare against)"
            details = details,
        )
    details['prev_size_bytes'] = prev_size_bytes
    delta = size - prev_size_bytes
    relative = delta / prev_size_bytes if prev_size_bytes else 0
    details['delta_bytes'] = delta
    details['relative change'] = round(relative, 3)

    if relative > BUNDLE_SIZE_WARNING_THRESHOLD:
        return CheckResult(
            name="bundle_size",
            status="warning",
            summary=f"Bundle grew {relative:.0%} vs previous releases ({prev_size_bytes:,} -> {size:,} bytes)."
            details=details,
        )
    

def check_compatible_host_versions(range_str: str):
    return 'none'

def check_dangerous_patterns(js_files) -> CheckResult:
    patterns = {
        "eval_or_function_constructor": re.compile(r"\beval\s*\(|\bnew\s+Function\s*\("),
        "innerHTML_assignment" : re.compile(r"\.innerHTML\s*="),
        "document_cookies": re.compile(r"\b(localStorage|sessionStorage)\b")
    }

    findings={}
    for label, pattern in patterns.items():
        matches = _find_files_with_pattern(js_files, pattern)

        if matches:
            findings[label] = matches

    if not findings:
        return CheckResult(
            name="dangerous_patterns",
            status="pass",
            summary="No eval/Function, innerHTML assignment, document.cookie, or Web Storage usage detected.",
        )
    
    return CheckResult(
        name="dangerous_patterns",
        status="warning",
        summary=f"Found{sum(len(v) for v in findings.values())} occurrence(s) across {len(findings)} pattern(s) - need reviewer judgemnet.",
        details=findings,
    )
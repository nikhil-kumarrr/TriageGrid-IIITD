/** Shared brand for every application screen. Keep favicon and mark asset identical. */
export function Brand() {
  return <span className="brandIdentity" aria-label="TriageGrid">
    <img className="brandSymbol" src="/assets/triagegrid-mark.svg" alt="" width="42" height="42"/>
    <span className="brandWordmark" aria-hidden="true">Triage<span>Grid</span></span>
  </span>;
}

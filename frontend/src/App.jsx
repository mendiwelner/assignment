import { useEffect, useMemo, useState } from 'react';

const API_BASE = '/api';
const DEFAULT_PAGE_SIZE = 10;
const AGGREGATION_PAGE_SIZE = 5;

function App() {
  const [items, setItems] = useState([]);
  const [pagination, setPagination] = useState({ page: 1, page_size: DEFAULT_PAGE_SIZE, total: 0, pages: 0 });
  const [aggregation, setAggregation] = useState([]);
  const [aggregationPagination, setAggregationPagination] = useState({
    page: 1,
    page_size: AGGREGATION_PAGE_SIZE,
    total: 0,
    pages: 0,
  });
  const [loadingReadings, setLoadingReadings] = useState(false);
  const [loadingAggregation, setLoadingAggregation] = useState(false);
  const [filters, setFilters] = useState({
    asset_id: '',
    asset_type: '',
    metric: '',
    status: '',
    start_time: '',
    end_time: '',
  });
  const [page, setPage] = useState(1);
  const [aggregationPage, setAggregationPage] = useState(1);

  const filterParams = useMemo(() => {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value) params.set(key, value);
    });
    return params;
  }, [filters]);

  const readingsQueryString = useMemo(() => {
    const params = new URLSearchParams(filterParams);
    params.set('page', String(page));
    params.set('page_size', String(DEFAULT_PAGE_SIZE));
    return params.toString();
  }, [filterParams, page]);

  const aggregationQueryString = useMemo(() => {
    const params = new URLSearchParams(filterParams);
    params.set('page', String(aggregationPage));
    params.set('page_size', String(AGGREGATION_PAGE_SIZE));
    return params.toString();
  }, [filterParams, aggregationPage]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      const loadReadings = async () => {
        setLoadingReadings(true);
        try {
          const response = await fetch(`${API_BASE}/readings?${readingsQueryString}`);
          const payload = await response.json();
          setItems(payload.items ?? []);
          setPagination(payload.pagination ?? { page, page_size: DEFAULT_PAGE_SIZE, total: 0, pages: 0 });
        } finally {
          setLoadingReadings(false);
        }
      };

      loadReadings();
    }, 300);

    return () => window.clearTimeout(timer);
  }, [readingsQueryString, page]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      const loadAggregation = async () => {
        setLoadingAggregation(true);
        try {
          const response = await fetch(`${API_BASE}/aggregation?${aggregationQueryString}`);
          const payload = await response.json();
          setAggregation(payload.items ?? []);
          setAggregationPagination(
            payload.pagination ?? {
              page: aggregationPage,
              page_size: AGGREGATION_PAGE_SIZE,
              total: 0,
              pages: 0,
            },
          );
        } finally {
          setLoadingAggregation(false);
        }
      };

      loadAggregation();
    }, 300);

    return () => window.clearTimeout(timer);
  }, [aggregationQueryString, aggregationPage]);

  const handleFilterChange = (event) => {
    const { name, value } = event.target;
    setPage(1);
    setAggregationPage(1);
    setFilters((current) => ({ ...current, [name]: value }));
  };

  const resetFilters = () => {
    setPage(1);
    setAggregationPage(1);
    setFilters({ asset_id: '', asset_type: '', metric: '', status: '', start_time: '', end_time: '' });
  };

  return (
    <div className="app-shell">
      <header className="hero">
        <div>
          <p className="eyebrow">Sensor Telemetry Explorer</p>
          <h1>Inspect live telemetry with fast server-side filtering.</h1>
        </div>
        <div className="hero-badge">{pagination.total} readings</div>
      </header>

      <section className="panel controls">
        <div className="control-grid">
          <label>
            Asset ID
            <input name="asset_id" value={filters.asset_id} onChange={handleFilterChange} placeholder="PS-042" />
          </label>
          <label>
            Asset Type
            <select name="asset_type" value={filters.asset_type} onChange={handleFilterChange}>
              <option value="">All</option>
              <option value="pump_station">Pump station</option>
              <option value="borehole">Borehole</option>
              <option value="reservoir">Reservoir</option>
            </select>
          </label>
          <label>
            Metric
            <select name="metric" value={filters.metric} onChange={handleFilterChange}>
              <option value="">All</option>
              <option value="flow_rate">Flow rate</option>
              <option value="pressure">Pressure</option>
              <option value="energy_kwh">Energy</option>
              <option value="water_level">Water level</option>
            </select>
          </label>
          <label>
            Status
            <select name="status" value={filters.status} onChange={handleFilterChange}>
              <option value="">All</option>
              <option value="ok">Ok</option>
              <option value="warning">Warning</option>
              <option value="fault">Fault</option>
            </select>
          </label>
          <label>
            From
            <input name="start_time" type="datetime-local" value={filters.start_time} onChange={handleFilterChange} />
          </label>
          <label>
            To
            <input name="end_time" type="datetime-local" value={filters.end_time} onChange={handleFilterChange} />
          </label>
        </div>
        <div className="controls-actions">
          <button type="button" onClick={resetFilters}>Reset</button>
        </div>
      </section>

      <section className="layout-grid">
        <div className="panel summary">
          <div className="table-header">
            <h2>Aggregation snapshot</h2>
            <span>{aggregationPagination.pages} pages</span>
          </div>
          {loadingAggregation ? (
            <p className="empty-state">Loading aggregation...</p>
          ) : aggregation.length > 0 ? (
            <>
              <ul className="aggregate-list">
                {aggregation.map((entry) => (
                  <li key={`${entry.asset_id}-${entry.metric}`}>
                    <div>
                      <strong>{entry.asset_id}</strong>
                      <span>{entry.metric}</span>
                    </div>
                    <div>
                      <span>Avg {entry.average}</span>
                      <span>Min {entry.minimum}</span>
                      <span>Max {entry.maximum}</span>
                    </div>
                  </li>
                ))}
              </ul>
              <div className="pagination">
                <button
                  type="button"
                  onClick={() => setAggregationPage((current) => Math.max(1, current - 1))}
                  disabled={aggregationPage === 1}
                >
                  Prev
                </button>
                <span>Page {aggregationPagination.page}</span>
                <button
                  type="button"
                  onClick={() => setAggregationPage((current) => current + 1)}
                  disabled={aggregationPage >= aggregationPagination.pages}
                >
                  Next
                </button>
              </div>
            </>
          ) : (
            <p className="empty-state">No aggregation rows matched the active filters.</p>
          )}
        </div>

        <div className="panel table-panel">
          <div className="table-header">
            <h2>Readings</h2>
            <span>{pagination.pages} pages</span>
          </div>

          {loadingReadings ? (
            <p className="empty-state">Loading telemetry...</p>
          ) : items.length === 0 ? (
            <p className="empty-state">Nothing matched these filters.</p>
          ) : (
            <>
              <table>
                <thead>
                  <tr>
                    <th>Asset</th>
                    <th>Metric</th>
                    <th>Value</th>
                    <th>Status</th>
                    <th>Recorded</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((item) => (
                    <tr key={item.id}>
                      <td>{item.asset_id}</td>
                      <td>{item.metric}</td>
                      <td>{item.value} {item.unit}</td>
                      <td>{item.status}</td>
                      <td>{item.recorded_at}</td>
                    </tr>
                  ))}
                </tbody>
              </table>

              <div className="pagination">
                <button type="button" onClick={() => setPage((current) => Math.max(1, current - 1))} disabled={page === 1}>
                  Prev
                </button>
                <span>Page {pagination.page}</span>
                <button type="button" onClick={() => setPage((current) => current + 1)} disabled={page >= pagination.pages}>
                  Next
                </button>
              </div>
            </>
          )}
        </div>
      </section>
    </div>
  );
}

export default App;

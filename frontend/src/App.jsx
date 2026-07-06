import { useEffect, useMemo, useState } from 'react';
import {
  Box,
  Button,
  Chip,
  CircularProgress,
  Container,
  FormControl,
  Grid,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';

const API_BASE = '/api';
const DEFAULT_PAGE_SIZE = 10;
const AGGREGATION_PAGE_SIZE = 5;

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: { main: '#1565c0' },
    background: { default: '#f4f6f8' },
  },
});

const STATUS_COLOR = {
  ok: 'success',
  warning: 'warning',
  fault: 'error',
};

function AppContent() {
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
    <Box sx={{ bgcolor: 'background.default', minHeight: '100vh', py: 4 }}>
      <Container maxWidth="xl">
        <Stack spacing={3}>
          <Paper sx={{ p: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
            <Box>
              <Typography variant="overline" color="primary" fontWeight={700}>
                Sensor Telemetry Explorer
              </Typography>
              <Typography variant="h5" component="h1" fontWeight={600}>
                Inspect live telemetry with fast server-side filtering
              </Typography>
            </Box>
            <Chip label={`${pagination.total.toLocaleString()} readings`} color="primary" variant="outlined" />
          </Paper>

          <Paper sx={{ p: 3 }}>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6} md={4} lg={2}>
                <TextField
                  fullWidth
                  size="small"
                  label="Asset ID"
                  name="asset_id"
                  value={filters.asset_id}
                  onChange={handleFilterChange}
                  placeholder="PS-042"
                />
              </Grid>
              <Grid item xs={12} sm={6} md={4} lg={2}>
                <FormControl fullWidth size="small">
                  <InputLabel>Asset Type</InputLabel>
                  <Select name="asset_type" value={filters.asset_type} label="Asset Type" onChange={handleFilterChange}>
                    <MenuItem value="">All</MenuItem>
                    <MenuItem value="pump_station">Pump station</MenuItem>
                    <MenuItem value="borehole">Borehole</MenuItem>
                    <MenuItem value="reservoir">Reservoir</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} sm={6} md={4} lg={2}>
                <FormControl fullWidth size="small">
                  <InputLabel>Metric</InputLabel>
                  <Select name="metric" value={filters.metric} label="Metric" onChange={handleFilterChange}>
                    <MenuItem value="">All</MenuItem>
                    <MenuItem value="flow_rate">Flow rate</MenuItem>
                    <MenuItem value="pressure">Pressure</MenuItem>
                    <MenuItem value="energy_kwh">Energy</MenuItem>
                    <MenuItem value="water_level">Water level</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} sm={6} md={4} lg={2}>
                <FormControl fullWidth size="small">
                  <InputLabel>Status</InputLabel>
                  <Select name="status" value={filters.status} label="Status" onChange={handleFilterChange}>
                    <MenuItem value="">All</MenuItem>
                    <MenuItem value="ok">Ok</MenuItem>
                    <MenuItem value="warning">Warning</MenuItem>
                    <MenuItem value="fault">Fault</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} sm={6} md={4} lg={2}>
                <TextField
                  fullWidth
                  size="small"
                  label="From"
                  name="start_time"
                  type="datetime-local"
                  value={filters.start_time}
                  onChange={handleFilterChange}
                  InputLabelProps={{ shrink: true }}
                />
              </Grid>
              <Grid item xs={12} sm={6} md={4} lg={2}>
                <TextField
                  fullWidth
                  size="small"
                  label="To"
                  name="end_time"
                  type="datetime-local"
                  value={filters.end_time}
                  onChange={handleFilterChange}
                  InputLabelProps={{ shrink: true }}
                />
              </Grid>
            </Grid>
            <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
              <Button variant="outlined" onClick={resetFilters}>
                Reset
              </Button>
            </Box>
          </Paper>

          <Grid container spacing={3}>
            <Grid item xs={12} lg={4}>
              <Paper sx={{ p: 3, height: '100%' }}>
                <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 2 }}>
                  <Typography variant="h6">Aggregation snapshot</Typography>
                  <Typography variant="body2" color="text.secondary">
                    {aggregationPagination.pages} pages
                  </Typography>
                </Stack>

                {loadingAggregation ? (
                  <Box sx={{ display: 'flex', justifyContent: 'center', py: 6 }}>
                    <CircularProgress size={32} />
                  </Box>
                ) : aggregation.length > 0 ? (
                  <>
                    <Stack spacing={1.5}>
                      {aggregation.map((entry) => (
                        <Paper key={`${entry.asset_id}-${entry.metric}`} variant="outlined" sx={{ p: 2 }}>
                          <Stack direction="row" justifyContent="space-between" alignItems="center" flexWrap="wrap" gap={1}>
                            <Box>
                              <Typography fontWeight={700}>{entry.asset_id}</Typography>
                              <Typography variant="body2" color="text.secondary">
                                {entry.metric}
                              </Typography>
                            </Box>
                            <Stack direction="row" spacing={1} flexWrap="wrap">
                              <Chip size="small" label={`Avg ${entry.average}`} />
                              <Chip size="small" label={`Min ${entry.minimum}`} variant="outlined" />
                              <Chip size="small" label={`Max ${entry.maximum}`} variant="outlined" />
                            </Stack>
                          </Stack>
                        </Paper>
                      ))}
                    </Stack>
                    <Stack direction="row" justifyContent="center" alignItems="center" spacing={2} sx={{ mt: 2 }}>
                      <Button
                        size="small"
                        variant="outlined"
                        onClick={() => setAggregationPage((current) => Math.max(1, current - 1))}
                        disabled={aggregationPage === 1}
                      >
                        Prev
                      </Button>
                      <Typography variant="body2">Page {aggregationPagination.page}</Typography>
                      <Button
                        size="small"
                        variant="outlined"
                        onClick={() => setAggregationPage((current) => current + 1)}
                        disabled={aggregationPage >= aggregationPagination.pages}
                      >
                        Next
                      </Button>
                    </Stack>
                  </>
                ) : (
                  <Typography color="text.secondary" sx={{ py: 4, textAlign: 'center' }}>
                    No aggregation rows matched the active filters.
                  </Typography>
                )}
              </Paper>
            </Grid>

            <Grid item xs={12} lg={8}>
              <Paper sx={{ p: 3 }}>
                <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 2 }}>
                  <Typography variant="h6">Readings</Typography>
                  <Typography variant="body2" color="text.secondary">
                    {pagination.pages} pages
                  </Typography>
                </Stack>

                {loadingReadings ? (
                  <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
                    <CircularProgress size={40} />
                  </Box>
                ) : items.length === 0 ? (
                  <Typography color="text.secondary" sx={{ py: 8, textAlign: 'center' }}>
                    Nothing matched these filters.
                  </Typography>
                ) : (
                  <>
                    <TableContainer>
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            <TableCell>Asset</TableCell>
                            <TableCell>Metric</TableCell>
                            <TableCell>Value</TableCell>
                            <TableCell>Status</TableCell>
                            <TableCell>Recorded</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {items.map((item) => (
                            <TableRow key={item.id} hover>
                              <TableCell>{item.asset_id}</TableCell>
                              <TableCell>{item.metric}</TableCell>
                              <TableCell>
                                {item.value} {item.unit}
                              </TableCell>
                              <TableCell>
                                <Chip
                                  size="small"
                                  label={item.status}
                                  color={STATUS_COLOR[item.status] ?? 'default'}
                                />
                              </TableCell>
                              <TableCell>{item.recorded_at}</TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>

                    <Stack direction="row" justifyContent="center" alignItems="center" spacing={2} sx={{ mt: 2 }}>
                      <Button
                        variant="outlined"
                        onClick={() => setPage((current) => Math.max(1, current - 1))}
                        disabled={page === 1}
                      >
                        Prev
                      </Button>
                      <Typography variant="body2">Page {pagination.page}</Typography>
                      <Button
                        variant="outlined"
                        onClick={() => setPage((current) => current + 1)}
                        disabled={page >= pagination.pages}
                      >
                        Next
                      </Button>
                    </Stack>
                  </>
                )}
              </Paper>
            </Grid>
          </Grid>
        </Stack>
      </Container>
    </Box>
  );
}

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AppContent />
    </ThemeProvider>
  );
}

export default App;

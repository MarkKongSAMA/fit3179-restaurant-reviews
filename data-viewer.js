'use strict';

// This page reads the same processed files as the charts. It does not fetch live
// restaurant data or modify the data. All record values are rendered as text.
(() => {
  const VENUE_SOURCE = 'https://data.melbourne.vic.gov.au/explore/dataset/cafes-and-restaurants-with-seating-capacity/';
  const AREA_SOURCE = 'https://data.melbourne.vic.gov.au/explore/dataset/small-areas-for-census-of-land-use-and-employment-clue/';
  const REVIEW_SOURCE = 'https://www.tripadvisor.com.au/Restaurants-g255100-Melbourne_Victoria.html';
  const PAGE_SIZE = 25;
  const formatNumber = new Intl.NumberFormat('en-AU');
  const $ = id => document.getElementById(id);

  const datasets = {
    reviews: {
      title: 'Selected restaurant reviews',
      file: 'reviews.json',
      period: 'REVIEW LISTINGS · ACCESSED 6 OCTOBER 2026',
      description: 'A non-random sample of 31 Melbourne restaurant listings: 25 featured listings encountered on Tripadvisor plus six selected fine-dining listings. Each row represents one listing.',
      caveat: 'Ratings and cumulative review counts describe this selected sample, not all Melbourne restaurants. Reader snapshots may be cached. Price bands are not dollar prices; dietary tags are listing claims. Only 27 locations have a reliable match to the historical census.',
      placeholder: 'Name, cuisine, price, address or dietary tag',
      sources: [{ label: 'Tripadvisor Melbourne listings', url: REVIEW_SOURCE }],
      columns: [
        { key: 'name', label: 'Restaurant / source', type: 'listing', width: '25%' },
        { key: 'rating', label: 'Rating / 5', type: 'decimal', digits: 1, width: '8%' },
        { key: 'review_count', label: 'Reviews', type: 'number', width: '9%' },
        { key: 'price', label: 'Price band', width: '12%' },
        { key: 'cuisines', label: 'Cuisine tags', width: '21%' },
        { key: 'diets', label: 'Listed dietary tags', width: '25%' },
      ],
    },
    venues: {
      title: 'Official café and restaurant venues',
      file: 'venues.json',
      period: 'CITY OF MELBOURNE · 2024 CLUE CENSUS',
      description: 'The official café and restaurant industry records, combined into 1,645 establishment locations. Indoor and outdoor seating rows are grouped by property, business name and address.',
      caveat: 'These are historical 2024 establishment records, not a current business directory. A location record is not a unique restaurant brand. CLUE statistical areas differ from suburbs and postcodes.',
      placeholder: 'Venue name, street address or CLUE area',
      sources: [{ label: 'City of Melbourne venue dataset', url: VENUE_SOURCE }],
      columns: [
        { key: 'name', label: 'Venue', width: '24%' },
        { key: 'address', label: 'Recorded address', width: '31%' },
        { key: 'area', label: 'CLUE area', width: '20%' },
        { key: 'seats', label: 'Total seats', type: 'number', width: '9%' },
        { label: 'Original source', type: 'source', url: VENUE_SOURCE, text: 'City of Melbourne', width: '16%' },
      ],
    },
    areas: {
      title: 'Dining density by CLUE area',
      file: 'areas.geojson',
      geojson: true,
      period: 'OFFICIAL CLUE BOUNDARIES · VENUE COUNTS FOR 2024',
      description: 'Thirteen statistical areas with establishment counts and calculated density. Density is the 2024 venue count divided by the full polygon area in square kilometres.',
      caveat: 'Areas include parks, water and industrial land. They are not gazetted suburbs. Polygon areas are calculated in UTM zone 55S; source boundary processing dates are separate from the 2024 venue census.',
      placeholder: 'CLUE area name or recorded numeric value',
      sources: [{ label: 'Official CLUE boundaries', url: AREA_SOURCE }, { label: '2024 venue records', url: VENUE_SOURCE }],
      columns: [
        { key: 'area', label: 'CLUE area', width: '28%' },
        { key: 'venue_count', label: 'Venues', type: 'number', width: '13%' },
        { key: 'area_km2', label: 'Area (km²)', type: 'decimal', digits: 3, width: '17%' },
        { key: 'density', label: 'Venues / km²', type: 'decimal', digits: 2, width: '18%' },
        { label: 'Original geography', type: 'source', url: AREA_SOURCE, text: 'CLUE boundaries', width: '24%' },
      ],
    },
    grids: {
      title: 'Dining clusters in 500 m cells',
      file: 'grids.geojson',
      geojson: true,
      period: 'DERIVED FROM 2024 CLUE VENUE LOCATIONS',
      description: 'Eighty-seven occupied 500 × 500 m grid cells containing the 1,645 official establishment records. Each full square covers 0.25 km². Easting and northing identify the cell’s southwest corner in UTM zone 55S, in metres.',
      caveat: 'Only occupied cells are included. Full squares are retained at the municipal edge to preserve equal areas; a cell can extend beyond the boundary. Counts refer only to locations in the official covered area.',
      placeholder: 'Cell ID, venue count, easting or northing',
      sources: [{ label: 'City of Melbourne venue locations', url: VENUE_SOURCE }],
      columns: [
        { key: 'id', label: 'Cell ID', width: '17%' },
        { key: 'count', label: 'Venues', type: 'number', width: '12%' },
        { key: 'cell_width_m', label: 'Cell side (m)', type: 'number', width: '14%' },
        { key: 'easting', label: 'UTM easting (m)', type: 'number', width: '17%' },
        { key: 'northing', label: 'UTM northing (m)', type: 'number', width: '18%' },
        { label: 'Original locations', type: 'source', url: VENUE_SOURCE, text: 'City of Melbourne', width: '22%' },
      ],
    },
  };

  const requested = new URLSearchParams(window.location.search).get('dataset');
  const key = Object.prototype.hasOwnProperty.call(datasets, requested) ? requested : 'reviews';
  const config = datasets[key];
  let records = [];
  let indexedRows = [];
  let matchingRows = [];
  let page = 0;
  let loading = false;

  function safeLink(url, text) {
    try {
      const parsed = new URL(url);
      if (parsed.protocol !== 'https:' && parsed.protocol !== 'http:') return null;
      const link = document.createElement('a');
      link.href = parsed.href;
      link.target = '_blank';
      link.rel = 'noopener noreferrer';
      link.textContent = text + ' ↗';
      return link;
    } catch (_) {
      return null;
    }
  }

  function displayValue(value, column) {
    if (value === null || value === undefined || value === '' || (Array.isArray(value) && value.length === 0)) return 'Not recorded';
    if (Array.isArray(value)) return value.join('; ');
    if (column.type === 'decimal' && Number.isFinite(value)) return value.toLocaleString('en-AU', { minimumFractionDigits: column.digits, maximumFractionDigits: column.digits });
    if (column.type === 'number' && Number.isFinite(value)) return formatNumber.format(value);
    return String(value);
  }

  function setOverview() {
    document.title = config.title + ' · Beyond the Stars';
    $('dataset-title').textContent = config.title;
    $('dataset-period').textContent = config.period;
    $('dataset-description').textContent = config.description;
    $('dataset-caveat').textContent = config.caveat;
    $('data-search').placeholder = config.placeholder;
    $('csv-download').href = 'data/downloads/' + key + '.csv';
    $('csv-download').download = key + '.csv';
    $('original-download').href = 'data/processed/' + config.file;
    $('original-download').download = config.file;
    $('original-download').textContent = 'Download original ' + (config.geojson ? 'GeoJSON' : 'JSON') + ' ↓';
    $('format-note').textContent = config.geojson
      ? 'The preview shows selected fields. CSV includes additional fields and geometry as text for inspection. Use the original GeoJSON, which preserves feature geometry, for mapping.'
      : 'The preview shows selected fields. CSV includes additional fields for spreadsheet use. Original JSON preserves the data structure used by the website.';
    $('table-caption').textContent = config.title + ': selected fields. Empty source values appear as “Not recorded”.';

    document.querySelectorAll('[data-dataset]').forEach(link => {
      if (link.dataset.dataset === key) link.setAttribute('aria-current', 'page');
      else link.removeAttribute('aria-current');
    });
    const sources = $('dataset-sources');
    sources.replaceChildren(document.createTextNode('Source: '));
    config.sources.forEach((source, index) => {
      if (index) sources.append(document.createTextNode(' · '));
      const link = safeLink(source.url, source.label);
      if (link) sources.append(link);
    });
    const headerRow = document.createElement('tr');
    config.columns.forEach(column => {
      const heading = document.createElement('th');
      heading.scope = 'col';
      heading.textContent = column.label;
      heading.style.width = column.width;
      headerRow.append(heading);
    });
    $('data-head').replaceChildren(headerRow);
  }

  function makeCell(row, column) {
    const cell = document.createElement('td');
    cell.dataset.label = column.label;
    if (column.type === 'source') {
      const link = safeLink(column.url, column.text);
      if (link) cell.append(link);
      else cell.textContent = 'Not recorded';
    } else if (column.type === 'listing') {
      const name = displayValue(row.name, column);
      const link = safeLink(row.source_url, name);
      if (link) cell.append(link);
      else cell.textContent = name;
      const address = document.createElement('span');
      address.className = 'resource-cell-detail';
      address.textContent = displayValue(row.address, {});
      cell.append(address);
    } else {
      cell.textContent = displayValue(row[column.key], column);
    }
    return cell;
  }

  function renderPage() {
    const pageCount = Math.max(1, Math.ceil(matchingRows.length / PAGE_SIZE));
    page = Math.min(page, pageCount - 1);
    const start = page * PAGE_SIZE;
    const visible = matchingRows.slice(start, start + PAGE_SIZE);
    const body = $('data-rows');
    const fragment = document.createDocumentFragment();
    visible.forEach(row => {
      const tr = document.createElement('tr');
      config.columns.forEach(column => tr.append(makeCell(row, column)));
      fragment.append(tr);
    });
    if (visible.length === 0) {
      const tr = document.createElement('tr');
      tr.className = 'resource-empty-row';
      const td = document.createElement('td');
      td.colSpan = config.columns.length;
      td.textContent = 'No records match your search. Try fewer words or clear the search.';
      tr.append(td);
      fragment.append(tr);
    }
    body.replaceChildren(fragment);
    const range = visible.length ? formatNumber.format(start + 1) + '–' + formatNumber.format(start + visible.length) : '0';
    $('record-status').textContent = 'Showing ' + range + ' of ' + formatNumber.format(matchingRows.length) + ' matching records · ' + formatNumber.format(records.length) + ' records in this dataset';
    $('page-status').textContent = 'Page ' + (page + 1) + ' of ' + pageCount;
    $('previous-page').disabled = page === 0;
    $('next-page').disabled = page + 1 >= pageCount;
    $('clear-search').disabled = $('data-search').value.length === 0;
  }

  function applySearch() {
    const terms = $('data-search').value.trim().toLocaleLowerCase('en-AU').split(/\s+/).filter(Boolean);
    matchingRows = terms.length
      ? indexedRows.filter(item => terms.every(term => item.text.includes(term))).map(item => item.row)
      : records;
    page = 0;
    renderPage();
  }

  async function loadData() {
    if (loading) return;
    loading = true;
    $('data-error').hidden = true;
    $('record-status').textContent = 'Loading records…';
    $('data-search').disabled = true;
    $('clear-search').disabled = true;
    $('previous-page').disabled = true;
    $('next-page').disabled = true;
    $('retry-load').disabled = true;
    try {
      const response = await fetch('data/processed/' + config.file);
      if (!response.ok) throw new Error('Dataset request failed: ' + response.status);
      const source = await response.json();
      records = config.geojson ? source.features.map(feature => ({ ...feature.properties })) : source;
      if (!Array.isArray(records)) throw new Error('Dataset is not a record list');
      indexedRows = records.map(row => ({ row, text: Object.values(row).map(value => value == null ? '' : Array.isArray(value) ? value.join(' ') : String(value)).join(' ').toLocaleLowerCase('en-AU') }));
      $('preview-table-wrap').hidden = false;
      $('data-search').disabled = false;
      applySearch();
    } catch (error) {
      $('preview-table-wrap').hidden = true;
      $('data-error').hidden = false;
      $('data-error-message').textContent = 'The dataset could not load. Open this page through the local website address, then try again. Download links remain available above.';
      $('record-status').textContent = 'Data preview unavailable.';
      $('page-status').textContent = 'No page loaded';
      console.error(error);
    } finally {
      loading = false;
      $('retry-load').disabled = false;
    }
  }

  setOverview();
  $('search-form').addEventListener('submit', event => event.preventDefault());
  $('data-search').addEventListener('input', applySearch);
  $('clear-search').addEventListener('click', () => { $('data-search').value = ''; applySearch(); $('data-search').focus(); });
  $('previous-page').addEventListener('click', () => { if (page > 0) { page -= 1; renderPage(); } });
  $('next-page').addEventListener('click', () => { if ((page + 1) * PAGE_SIZE < matchingRows.length) { page += 1; renderPage(); } });
  $('retry-load').addEventListener('click', loadData);
  loadData();
})();

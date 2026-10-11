'use strict';
// Vega owns all data marks. HTML provides the story, controls and accessible source table.
const chartFiles = ['01-venue-density.vl.json','02-review-footprint.vl.json','03-dining-clusters.vl.json','04-rating-histogram.vl.json','05-rating-attention.vl.json','06-price-boxplot.vl.json','07-cuisine-price.vl.json','08-dietary-options.vl.json','09-budget-grid.vl.json','10-review-treemap.vg.json','11-diet-overlap.vg.json','12-shortlist.vl.json'];
const views = new Map();
let allReviews = [], brush = {}, updating = false, pendingUpdate = false, pendingScatter = false;
const $ = id => document.getElementById(id);
const number = value => value.toLocaleString('en-AU');
const inputs = [$('price'),$('minimum'),$('diet')];
const orderListings = (a,b) => b.rating-a.rating || b.review_count-a.review_count || a.name.localeCompare(b.name,'en');
function baseRows(){return allReviews.filter(d=>($('price').value==='all'||d.price===$('price').value)&&d.review_count>=Number($('minimum').value)&&($('diet').value==='all'||d.diets.includes($('diet').value)));}
function brushedRows(rows){return rows.filter(d=>Object.entries(brush).every(([field,extent])=>!Array.isArray(extent)||extent.length!==2||(d[field]>=extent[0]&&d[field]<=extent[1])));}
function updateTable(rows){
  const body=$('listing-rows');body.replaceChildren();
  [...rows].sort(orderListings).forEach(d=>{const row=document.createElement('tr');const name=document.createElement('td');const link=document.createElement('a');link.href=d.source_url;link.target='_blank';link.rel='noopener';link.textContent=d.name+' ↗';name.append(link);row.append(name);[d.rating.toFixed(1),number(d.review_count),d.price,d.diets.length?d.diets.join('; '):'No tags recorded (unknown)'].forEach(value=>{const td=document.createElement('td');td.textContent=value;row.append(td);});body.append(row);});
  if(!rows.length){const row=document.createElement('tr');const td=document.createElement('td');td.colSpan=5;td.textContent='No listings match these filters. Try a lower review threshold or reset all filters.';row.append(td);body.append(row);}
  $('table-count').textContent=`(${rows.length})`;
}
async function replaceRows(id,rows){const view=views.get(id);if(view) await view.change('reviews',vega.changeset().remove(()=>true).insert(rows.map(d=>({...d})))).runAsync();}
async function applyFilters(includeScatter=true){
  if(updating){pendingUpdate=true;pendingScatter ||= includeScatter;return;}
  updating=true;
  try{
    const base=baseRows(),selected=brushedRows(base),mapped=selected.filter(d=>Number.isFinite(d.longitude)&&Number.isFinite(d.latitude));
    await Promise.all([replaceRows(2,selected),replaceRows(12,selected),...(includeScatter?[replaceRows(5,base)]:[])]);
    $('chart-12').classList.toggle('empty',selected.length===0);
    $('chart-05').classList.toggle('empty',base.length===0);
    const brushed=Object.keys(brush).length>0;
    $('filter-status').textContent=`${selected.length} of 31 listings match · ${mapped.length} can be mapped${brushed?' · scatterplot brush active':''}${!selected.length?' — try broader filters.':''}`;
    $('map-note').textContent=`${mapped.length} of ${selected.length} matching listings have building-level locations from the 2024 census. Four uncertain locations in the full sample are omitted from this map only. These historical positions are not navigation advice.`;
    updateTable(selected);
  }catch(error){$('filter-status').textContent='A filter could not update. Please reload the page.';console.error(error);}finally{updating=false;if(pendingUpdate){const updateScatter=pendingScatter;pendingUpdate=false;pendingScatter=false;await applyFilters(updateScatter);}}
}
async function resetBrush(){brush={};const view=views.get(5);if(view){await view.change('brush_store',vega.changeset().remove(()=>true)).runAsync();}}
async function start(){
 inputs.forEach(input=>input.disabled=true);$('reset').disabled=true;
 try{
  const response=await fetch('data/processed/reviews.json');if(!response.ok)throw new Error('Review data unavailable');allReviews=await response.json();
  const results=await Promise.allSettled(chartFiles.map(async(file,index)=>{
    const id=index+1,element=$(`chart-${String(id).padStart(2,'0')}`);element.innerHTML='<p class="loading">Drawing the chart…</p>';
    const response=await fetch('specs/'+file);if(!response.ok)throw new Error(file+' unavailable');const spec=await response.json();
    // Relative data paths remain relative to this page, so every spec is independently readable.
    if([2,5,12].includes(id))spec.data.values=allReviews.map(d=>({...d}));
    const isVega=file.endsWith('.vg.json');if(isVega)spec.width=Math.max(250,element.clientWidth-16);
    const embedded=await vegaEmbed(element,spec,{actions:false,renderer:'svg',mode:isVega?'vega':'vega-lite',tooltip:{theme:'light'}});
    views.set(id,embedded.view);element.dataset.ready='true';
    if(isVega){new ResizeObserver(()=>{const width=Math.max(230,element.clientWidth-16);embedded.view.width(width).resize().runAsync();}).observe(element);}
  }));
  results.forEach((result,index)=>{if(result.status==='rejected'){console.error(result.reason);const element=$(`chart-${String(index+1).padStart(2,'0')}`);element.classList.add('chart-error');element.textContent='This chart could not load. Reload the page, or inspect its specification below.';}});
  if(views.get(5))views.get(5).addSignalListener('brush',(_name,value)=>{brush=value||{};applyFilters(false);});
  for(const input of inputs)input.addEventListener('change',async()=>{await resetBrush();await applyFilters();});
  $('reset').addEventListener('click',async()=>{inputs[0].value='all';inputs[1].value='0';inputs[2].value='all';await resetBrush();await applyFilters();});
  await applyFilters();
  inputs.forEach(input=>input.disabled=false);$('reset').disabled=false;
 }catch(error){$('filter-status').textContent='The data could not load. Open the site through its web address, then try again.';console.error(error);}
}
start();

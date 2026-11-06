"""Launch with streamlit run src/lastmile/dashboard.py."""
from pathlib import Path
import tempfile
from dataclasses import asdict
import json
import pandas as pd
import streamlit as st
from lastmile.simulation import Config, load_demand, simulate
from lastmile.experiments import policies
from lastmile.model import history, calendar, DemandModel
from lastmile.hourly import allocate_hourly

st.set_page_config(page_title='ISE450 Delivery Lab', layout='wide')
st.title('ISE450 Last-mile Delivery Lab')
st.caption('Synthetic demand → parcel queues → delivery vehicles → scenario comparisons')
st.info('All operations are assumptions. The 15% delay target is hypothetical. Results are simulation outputs, not measured company performance.')
with st.sidebar:
    st.header('Experiment controls')
    upload = st.file_uploader('Optional daily or hourly demand CSV', type='csv')
    sample = st.number_input('Demand sample ID', 0, 10000, 0)
    days = st.slider('Generated demand days', 1, 7, 2)
    seed = st.number_input('Random seed', 0, 1000000, 42)
    fleet = st.slider('Vehicles', 6, 100, 48)
    capacity = st.slider('Parcels per vehicle batch', 1, 60, 24)
    window = st.slider('Delivery window (hours)', .5, 24., 4., .5)
    service = st.slider('Service minutes per parcel', .5, 10., 3., .5)
    dispatch = st.slider('Dispatch interval (minutes)', 5, 60, 15, 5)
    speed = st.slider('District speed multiplier', .2, 1.5, 1., .05)
    selected = st.multiselect('Scenarios', list(policies(Config())), default=['normal', 'surge', 'typhoon', 'surge_typhoon'])
    run = st.button('Run simulation', type='primary')

@st.cache_data
def generated(days, seed, sample):
    rows, counts = history(days=365, seed=seed)
    model = DemandModel().fit(rows, counts)
    future = calendar('2026-01-01', days, seed+2)
    return allocate_hourly(model.sample(future, sample+1, seed), seed+3)[sample]

if run:
    if not selected:
        st.warning('Select at least one scenario.')
    else:
        try:
            if upload is not None:
                with tempfile.TemporaryDirectory() as tmp:
                    path = Path(tmp)/'input.csv'
                    path.write_bytes(upload.getvalue())
                    counts, meta = load_demand(path, sample)
            else:
                counts = generated(days, seed, sample)
                meta = {'source': 'built-in statistical generator; assumed hourly profile', 'sample_id': sample}
            cfg = Config(fleet=fleet, capacity=capacity, window_hours=window, service_minutes=service,
                         dispatch_minutes=dispatch, speed_factor=speed, seed=seed)
            results, traces = [], []
            with st.spinner('Running parcel deliveries…'):
                for name in selected:
                    r = simulate(counts, policies(cfg)[name], trace=True)
                    traces.extend({'scenario': name, **o} for o in r.pop('orders'))
                    results.append({'scenario': name, **r})
            meta.update(config=asdict(cfg), policies={name: asdict(policies(cfg)[name]) for name in selected})
            st.session_state['result'] = (results, traces, meta)
        except (ValueError, KeyError, OSError) as e:
            st.error(f'Cannot run input: {e}')
if 'result' in st.session_state:
    results, traces, meta = st.session_state['result']
    st.caption('Last completed run. Click Run simulation to apply changed controls. One replication: no uncertainty interval; use the CLI suite for inference.')
    frame = pd.DataFrame(results).set_index('scenario')
    first = results[0]
    columns = st.columns(3)
    columns[0].metric(f"{first['scenario']} delay rate", f"{first['delay_rate']:.1%}")
    columns[1].metric('Average delivery time', f"{first['avg_delivery_hours']:.2f} hours")
    columns[2].metric('Fleet utilization', f"{first['fleet_utilization']:.1%}")
    st.subheader('Scenario comparison')
    st.bar_chart(frame[['delay_rate', 'fleet_utilization']])
    st.bar_chart(frame[['avg_delivery_hours']])
    st.dataframe(frame, width='stretch')
    if traces:
        orders = pd.DataFrame(traces)
        orders['arrival_hour'] = orders.arrival_hours.astype(int)
        st.subheader('Delivery time by arrival hour')
        st.line_chart(orders.groupby(['arrival_hour','scenario']).delivery_hours.mean().unstack())
        st.subheader('District outcomes')
        st.dataframe(orders.groupby(['scenario','district']).agg(parcels=('delayed','size'), delay_rate=('delayed','mean'), avg_hours=('delivery_hours','mean')))
    st.download_button('Download metrics CSV', frame.to_csv(), 'simulation_metrics.csv', 'text/csv')
    st.download_button('Download parcel trace CSV', pd.DataFrame(traces).to_csv(index=False), 'orders.csv', 'text/csv')
    st.download_button('Download input details', json.dumps(meta, indent=2), 'input_details.json')
else:
    st.write('Choose controls and click **Run simulation**. Upload existing AI demand exports or use the built-in reproducible demo.')

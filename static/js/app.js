async function fetchState(){
  const res = await fetch(window.IOT.endpoints.state);
  const data = await res.json();
  if(!data.ok) return;

  const door = data.state['door_sala'];
  const temp = data.state['temp_sensor'];

  const dot = document.getElementById('doorStatusDot');
  const txt = document.getElementById('doorStatusText');
  const tempVal = document.getElementById('tempVal');

  if(door && dot && txt){
    if(door.state === 'ON'){
      dot.classList.remove('bg-danger'); dot.classList.add('bg-success');
      txt.textContent = 'ABIERTA';
    }else{
      dot.classList.remove('bg-success'); dot.classList.add('bg-danger');
      txt.textContent = 'CERRADA';
    }
  }
  if(temp && tempVal){
    tempVal.textContent = temp.reading;
  }
}

async function toggleDoor(){
  const btn = document.getElementById('toggleDoorBtn');
  btn.disabled = true;
  try{
    const res = await fetch(window.IOT.endpoints.toggleDoor, { method:'POST' });
    const data = await res.json();
    await fetchState();
  }catch(e){
    console.error(e);
  }finally{
    btn.disabled = false;
  }
}

document.addEventListener('DOMContentLoaded', () => {
  const refreshBtn = document.getElementById('refreshBtn');
  const toggleBtn = document.getElementById('toggleDoorBtn');
  if(refreshBtn) refreshBtn.addEventListener('click', fetchState);
  if(toggleBtn) toggleBtn.addEventListener('click', toggleDoor);
  fetchState();
});

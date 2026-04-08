/* ================================================================
   PARADISE RESORT — Enhanced JavaScript (All Features + Bug Fixes)
   ================================================================ */
'use strict';
const $  = id  => document.getElementById(id);
const $$ = sel => Array.from(document.querySelectorAll(sel));
const csrf = () => window.CSRF || '';

/* ── TOAST ── */
function toast(msg, type = 'success') {
  const wrap = $('toastWrap'); if (!wrap) return;
  const el = document.createElement('div');
  el.className = `toast toast-${type}`;
  el.textContent = msg;
  el.setAttribute('role','alert');
  el.setAttribute('aria-live','polite');
  wrap.appendChild(el);
  setTimeout(() => { el.style.transition='.35s'; el.style.opacity='0'; el.style.transform='translateX(110%)'; setTimeout(()=>el.remove(),400); }, 3200);
}

/* ── API ── */
async function api(url, body) {
  try {
    const r = await fetch(url, { method:'POST', headers:{'Content-Type':'application/json','X-CSRFToken':csrf()}, body: JSON.stringify({...body, csrf_token:csrf()}) });
    let data;
    try { data = await r.json(); }
    catch { data = { message: r.status === 403 ? 'Session expired. Please refresh the page.' : 'Server error. Please try again.' }; }
    return { ok:r.ok, status:r.status, data };
  } catch { return { ok:false, status:0, data:{message:'Network error — check your connection and try again.'} }; }
}
async function apiForm(url, fd) {
  try {
    fd.append('csrf_token', csrf());
    const r = await fetch(url, { method:'POST', headers:{'X-CSRFToken':csrf()}, body:fd });
    let data;
    try { data = await r.json(); }
    catch { data = { message: r.status === 403 ? 'Session expired. Please refresh the page.' : 'Server error. Please try again.' }; }
    return { ok:r.ok, status:r.status, data };
  } catch { return { ok:false, status:0, data:{message:'Network error — check your connection and try again.'} }; }
}

function showErr(id, msg) { const e=$(id); if(e){e.textContent=msg;e.style.display='block';e.scrollIntoView({behavior:'smooth',block:'nearest'});} }
function hideErr(id) { const e=$(id); if(e) e.style.display='none'; }
function setBtn(btn, on) {
  if (!btn) return; btn.disabled = on;
  const lbl=btn.querySelector('.btn-label'), spn=btn.querySelector('.btn-spin');
  if(lbl) lbl.style.display = on ? 'none' : '';
  if(spn) spn.style.display = on ? '' : 'none';
}

/* ── DARK MODE ── */
function initDarkMode() {
  const btn = $('themeToggle');
  if (!btn) return;
  const root = $('htmlRoot') || document.documentElement;
  function apply(t) {
    root.setAttribute('data-theme', t);
    localStorage.setItem('theme', t);
    btn.textContent = t === 'dark' ? '☀️ Light Mode' : '🌙 Dark Mode';
    btn.setAttribute('aria-label', t === 'dark' ? 'Switch to light mode' : 'Switch to dark mode');
  }
  apply(localStorage.getItem('theme') || 'light');
  btn.addEventListener('click', () => apply(root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark'));
}

/* ── SIDEBAR ── */
function initSidebar() {
  const openBtn=$('menuBtn'), closeBtn=$('sbClose'), sidebar=$('sidebar'), backdrop=$('sbBackdrop');
  if (!sidebar) return;
  const open = () => {
    sidebar.classList.add('open');
    backdrop?.classList.add('show');
    document.body.style.overflow='hidden';
    openBtn?.setAttribute('aria-expanded','true');
    closeBtn?.focus();
  };
  const close = () => {
    sidebar.classList.remove('open');
    backdrop?.classList.remove('show');
    document.body.style.overflow='';
    openBtn?.setAttribute('aria-expanded','false');
  };
  openBtn?.addEventListener('click', e => { e.stopPropagation(); sidebar.classList.contains('open') ? close() : open(); });
  closeBtn?.addEventListener('click', close);
  backdrop?.addEventListener('click', close);
  document.addEventListener('keydown', e => { if(e.key==='Escape') close(); });
  $$('.sb-link').forEach(a => a.addEventListener('click', () => { if(window.innerWidth<=900 && !a.dataset.tab) close(); }));
}

/* ── PARTICLES ── */
function initParticles() {
  const wrap = $('particles');
  if (!wrap || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  for (let i=0; i<22; i++) {
    const p = document.createElement('div'); p.className = 'particle'; p.setAttribute('aria-hidden','true');
    const sz = Math.random()*4+2;
    p.style.cssText = `left:${Math.random()*100}%;width:${sz}px;height:${sz}px;animation-duration:${Math.random()*14+8}s;animation-delay:${Math.random()*12}s`;
    wrap.appendChild(p);
  }
}

/* ── ADMIN COUNTERS ── */
function runCounters() {
  $$('.counter[data-to]').forEach(el => {
    const target = parseInt(el.dataset.to,10)||0;
    if (!target) { el.textContent='0'; return; }
    let cur=0;
    const id = setInterval(()=>{ cur=Math.min(cur+Math.max(1,target/60),target); el.textContent=Math.floor(cur).toLocaleString(); if(cur>=target){el.textContent=target.toLocaleString();clearInterval(id);} },16);
  });
}

/* ── ADMIN TABS ── */
function initAdminTabs() {
  const navLinks = $$('.sb-link[data-tab]');
  const tabBtns  = $$('.tab-nav[data-tab]');
  if (!navLinks.length) return;
  function activate(tabId) {
    navLinks.forEach(l => l.classList.toggle('active', l.dataset.tab===tabId));
    $$('.tab-section').forEach(s => { s.classList.remove('active'); s.hidden=true; });
    const panel = $('tab-'+tabId);
    if (panel) { panel.classList.add('active'); panel.hidden=false; if(tabId==='overview') setTimeout(runCounters,150); }
    if (window.innerWidth<=900) { $('sidebar')?.classList.remove('open'); $('sbBackdrop')?.classList.remove('show'); document.body.style.overflow=''; }
  }
  navLinks.forEach(l => l.addEventListener('click', e => { e.preventDefault(); activate(l.dataset.tab); }));
  tabBtns.forEach(b  => b.addEventListener('click',  e => { e.preventDefault(); activate(b.dataset.tab); }));
  if (document.querySelector('.tab-section.active#tab-overview')) setTimeout(runCounters,350);
}

/* ── AUTH (Login/Register) ── */
function initAuthPage() {
  const tabLogin=$('tabLogin'), tabReg=$('tabRegister'), loginSec=$('loginSection'), regSec=$('registerSection');
  const loginForm=$('loginForm'), regForm=$('registerForm');
  if (!loginForm && !regForm) return;

  const showLogin=()=>{loginSec&&(loginSec.style.display='');regSec&&(regSec.style.display='none');tabLogin?.classList.add('active');tabReg?.classList.remove('active');hideErr('loginErr');hideErr('regErr');tabLogin?.setAttribute('aria-selected','true');tabReg?.setAttribute('aria-selected','false');};
  const showReg=()=>{regSec&&(regSec.style.display='');loginSec&&(loginSec.style.display='none');tabReg?.classList.add('active');tabLogin?.classList.remove('active');hideErr('loginErr');hideErr('regErr');tabReg?.setAttribute('aria-selected','true');tabLogin?.setAttribute('aria-selected','false');};
  tabLogin?.addEventListener('click', showLogin);
  tabReg?.addEventListener('click',   showReg);

  [['eyeLogin','loginPass'],['eyeReg','regPass']].forEach(([bid,pid])=>{
    $(bid)?.addEventListener('click',function(){const p=$(pid);if(!p)return;p.type=p.type==='password'?'text':'password';this.textContent=p.type==='text'?'🙈':'👁';this.setAttribute('aria-label',p.type==='text'?'Hide password':'Show password');});
  });

  loginForm?.addEventListener('submit', async e => {
    e.preventDefault(); hideErr('loginErr');
    const u=($('loginUser')?.value||'').trim(), p=($('loginPass')?.value||'').trim();
    if (!u) { showErr('loginErr','⚠️ Please enter your username.'); return; }
    if (!p) { showErr('loginErr','⚠️ Please enter your password.'); return; }
    const btn=$('loginBtn'); setBtn(btn,true);
    const {ok,data}=await api(window.LOGIN_URL,{username:u,password:p});
    setBtn(btn,false);
    if (ok&&data.success) { toast(`Welcome back, ${u}! 🌴`); setTimeout(()=>{window.location.href=data.redirect;},700); }
    else showErr('loginErr','❌ '+(data.message||'Login failed.'));
  });

  regForm?.addEventListener('submit', async e => {
    e.preventDefault(); hideErr('regErr');
    const u=($('regUser')?.value||'').trim(), em=($('regEmail')?.value||'').trim(), p=($('regPass')?.value||'').trim(), c=($('regConfirm')?.value||'').trim();
    if (!u) { showErr('regErr','⚠️ Please enter a username.'); return; }
    if (u.length<3) { showErr('regErr','⚠️ Username must be at least 3 characters.'); return; }
    if (!p) { showErr('regErr','⚠️ Please enter a password.'); return; }
    if (p.length<6) { showErr('regErr','⚠️ Password must be at least 6 characters.'); return; }
    if (p!==c) { showErr('regErr','⚠️ Passwords do not match.'); return; }
    const btn=regForm.querySelector('button[type="submit"]'); setBtn(btn,true);
    const {ok,data}=await api(window.REGISTER_URL,{username:u,password:p,confirm:c,email:em});
    setBtn(btn,false);
    if (ok&&data.success) { toast('✅ Account created! Please log in.'); regForm.reset(); setTimeout(showLogin,900); }
    else showErr('regErr','❌ '+(data.message||'Registration failed.'));
  });

  $$('#loginForm .field-inp').forEach(inp=>inp.addEventListener('keydown',e=>{if(e.key==='Enter')loginForm.requestSubmit();}));
  $$('#registerForm .field-inp').forEach(inp=>inp.addEventListener('keydown',e=>{if(e.key==='Enter')regForm.requestSubmit();}));
}

/* ── DASHBOARD FILTER ── */
function initDashboardFilter() {
  const search=$('searchInput'), chips=$$('.fchip'), grid=$('cottageGrid'), noRes=$('noResults');
  if (!search||!grid) return;
  let af='all';
  function doFilter() {
    const q=search.value.toLowerCase().trim(); let visible=0;
    $$('.c-card').forEach(card=>{
      const mQ=!q||(card.dataset.name||'').includes(q);
      const p=parseFloat(card.dataset.price)||0;
      const mF=af==='budget'?p<1500:af==='mid'?p>=1500&&p<4000:af==='luxury'?p>=4000:true;
      card.style.display=mQ&&mF?'':'none'; if(mQ&&mF)visible++;
    });
    if(noRes) noRes.style.display=visible===0?'block':'none';
  }
  search.addEventListener('input',doFilter);
  chips.forEach(chip=>chip.addEventListener('click',()=>{ chips.forEach(c=>c.classList.remove('active')); chip.classList.add('active'); af=chip.dataset.f||'all'; doFilter(); }));
}

/* ── AVAILABILITY CHECKER ── */
function initAvailabilityChecker() {
  const btn=$('availBtn');
  if (!btn) return;
  btn.addEventListener('click', async () => {
    const cid=($('availCottage')?.value||'').trim(), dt=($('availDate')?.value||'').trim(), shift=($('availShift')?.value||'').trim();
    const res=$('availResult');
    if (!cid||!dt) { if(res){res.textContent='Please select a cottage and date.';res.className='avail-result avail-booked';res.style.display='block';} return; }
    btn.disabled=true; btn.textContent='Checking…';
    const url=`${window.AVAIL_URL}?cottage_id=${cid}&date=${dt}&shift=${encodeURIComponent(shift)}`;
    try {
      const r=await fetch(url); const d=await r.json();
      if(res){
        res.style.display='block';
        if(d.available){res.textContent='✅ Available! This slot is open for booking.';res.className='avail-result avail-available';}
        else{res.textContent='❌ Fully Booked. This slot is already taken.';res.className='avail-result avail-booked';}
      }
    } catch { if(res){res.textContent='Error checking availability.';res.className='avail-result avail-booked';res.style.display='block';} }
    btn.disabled=false; btn.textContent='Check';
  });
}

/* ── BOOKING CALENDAR ── */
function initBookingCalendar() {
  const calGrid=$('calGrid'), calTitle=$('calTitle'), calPrev=$('calPrev'), calNext=$('calNext'), bookDate=$('bookDate');
  if (!calGrid||!window.BOOKED_URL) return;
  let bookedData=[], today=new Date(), viewDate=new Date(today.getFullYear(),today.getMonth(),1);
  async function loadBooked() { try { const r=await fetch(window.BOOKED_URL); bookedData=await r.json(); } catch {} }
  function render() {
    const year=viewDate.getFullYear(), month=viewDate.getMonth();
    calTitle.textContent=new Date(year,month,1).toLocaleDateString('en-US',{month:'long',year:'numeric'});
    const days=['Su','Mo','Tu','We','Th','Fr','Sa'];
    const firstDay=new Date(year,month,1).getDay(), daysInMonth=new Date(year,month+1,0).getDate();
    let html=days.map(d=>`<div class="cal-day-header" aria-hidden="true">${d}</div>`).join('');
    for(let i=0;i<firstDay;i++) html+=`<div class="cal-day cal-empty" aria-hidden="true"></div>`;
    for(let d=1;d<=daysInMonth;d++){
      const dateStr=`${year}-${String(month+1).padStart(2,'0')}-${String(d).padStart(2,'0')}`;
      const dt=new Date(year,month,d), isPast=dt<new Date(today.getFullYear(),today.getMonth(),today.getDate());
      const isToday=dt.toDateString()===today.toDateString();
      const dayBooked=bookedData.filter(b=>b.date===dateStr);
      const hasDay=dayBooked.some(b=>b.shift.includes('Day')), hasNight=dayBooked.some(b=>b.shift.includes('Night'));
      let cls='cal-day', ariaLabel=dateStr;
      if (isToday) { cls+=' cal-today'; ariaLabel+=' (today)'; }
      if (isPast) { cls+=' cal-past'; ariaLabel+=' (past)'; }
      else if (hasDay&&hasNight) { cls+=' cal-full-booked'; ariaLabel+=' (fully booked)'; }
      else if (hasDay) { cls+=' cal-day-booked'; ariaLabel+=' (day booked)'; }
      else if (hasNight) { cls+=' cal-night-booked'; ariaLabel+=' (night booked)'; }
      else { cls+=' cal-free'; ariaLabel+=' (available)'; }
      const clickable=!isPast&&!(hasDay&&hasNight);
      html+=`<div class="${cls}" role="${clickable?'button':'presentation'}" ${clickable?`tabindex="0" onclick="selectCalDate('${dateStr}')" onkeydown="if(event.key==='Enter'||event.key===' ')selectCalDate('${dateStr}')"`:''} aria-label="${ariaLabel}">${d}</div>`;
    }
    calGrid.innerHTML=html;
  }
  window.selectCalDate=function(dateStr){ if(bookDate){ bookDate.value=dateStr; bookDate.dispatchEvent(new Event('change')); } };
  calPrev?.addEventListener('click',()=>{ viewDate.setMonth(viewDate.getMonth()-1); render(); });
  calNext?.addEventListener('click',()=>{ viewDate.setMonth(viewDate.getMonth()+1); render(); });
  loadBooked().then(render);
}

/* ── BOOKING PAGE ── */
function initBookingPage() {
  const form=$('bookingForm'); if(!form) return;
  const shiftGrid=$('shiftGrid'), payGrid=$('payGrid'), shiftInp=$('selectedShift'), payInp=$('selectedPay');
  const refGroup=$('refGroup'), refInput=$('refInput'), totalEl=$('totalPrice'), confirmBtn=$('confirmBtn');

  function updateTotal(){
    const night=(shiftInp?.value||'').includes('Night');
    const total=(window.BASE_PRICE||0)+(night?500:0);
    if(totalEl){totalEl.textContent='₱'+total.toLocaleString();totalEl.classList.remove('pop');void totalEl.offsetWidth;totalEl.classList.add('pop');}
  }

  shiftGrid?.querySelectorAll('.pick-card').forEach(card=>{
    card.addEventListener('click',()=>{
      shiftGrid.querySelectorAll('.pick-card').forEach(c=>c.classList.remove('active'));
      card.classList.add('active');
      if(shiftInp) shiftInp.value=card.dataset.val||'';
      updateTotal();
    });
  });

  payGrid?.querySelectorAll('.pick-card').forEach(card=>{
    card.addEventListener('click',()=>{
      payGrid.querySelectorAll('.pick-card').forEach(c=>c.classList.remove('active','pay-active'));
      card.classList.add('pay-active');
      if(payInp) payInp.value=card.dataset.val||'';
      const isBank=card.dataset.val==='bank';
      if(refGroup) refGroup.style.display=isBank?'':'none';
      if(!isBank&&refInput) refInput.value='';
      if(isBank&&refInput) setTimeout(()=>refInput.focus(),50);
    });
  });

  form.addEventListener('submit', async e=>{
    e.preventDefault(); hideErr('bookErr');
    const cid=($('cottageId')?.value||'').trim(), dt=($('bookDate')?.value||'').trim();
    const shift=(shiftInp?.value||'').trim(), pay=(payInp?.value||'').trim(), ref=(refInput?.value||'').trim();
    if(!dt){ showErr('bookErr','⚠️ Please select a date.'); return; }
    if(!shift){ showErr('bookErr','⚠️ Please select a shift.'); return; }
    if(!pay){ showErr('bookErr','⚠️ Please select a payment method.'); return; }
    if(pay==='bank'&&!ref){ showErr('bookErr','⚠️ Please enter your GCash/Bank reference number.'); return; }
    const num_guests=parseInt(document.getElementById('numGuests')?.value||'1');
    setBtn(confirmBtn,true);
    const {ok,data}=await api(window.CONFIRM_URL,{cottage_id:cid,date:dt,shift,payment:pay,reference:ref,num_guests});
    setBtn(confirmBtn,false);
    if(ok&&data.success) openReceipt(data.receipt, data.email_sent, data.guest_email);
    else showErr('bookErr','❌ '+(data.message||'Booking failed.'));
  });

  function openReceipt(r, emailSent, guestEmail){
    const modal=$('modalBg'), body=$('receiptRows'); if(!modal||!body) return;
    const rows=[
      ['Booking #','#'+r.id],
      ['Cottage',r.cottage],
      ['Guest',r.guest],
      ['Date',r.date],
      ['Shift',r.shift?.includes('Night')?'🌙 Night Tour':'☀️ Day Tour'],
      ['Guests',(r.num_guests||1)+' person'+((r.num_guests||1)>1?'s':'')],
      ['Payment',r.payment==='bank'?'📱 GCash/Bank':'💵 Cash'],
      r.reference?['Reference',r.reference]:null,
      ['TOTAL','₱'+Number(r.total).toLocaleString()]
    ].filter(Boolean);
    body.innerHTML=rows.map(([k,v])=>`<div class="r-row"><span>${k}</span><strong>${v}</strong></div>`).join('');

    // Email notice
    const notice=$('receiptEmailNotice');
    if(notice){
      if(emailSent && guestEmail){
        notice.innerHTML=`<span class="notice-icon">📧</span>
          <span>A confirmation receipt has been sent to <strong>${guestEmail}</strong></span>`;
        notice.className='receipt-email-notice receipt-email-sent';
      } else if(guestEmail && !emailSent){
        notice.innerHTML=`<span class="notice-icon">⚠️</span>
          <span>Could not send email to <strong>${guestEmail}</strong>. Please check your inbox later.</span>`;
        notice.className='receipt-email-notice receipt-email-warn';
      } else {
        notice.innerHTML=`<span class="notice-icon">💡</span>
          <span>Add your email in <a href="/auth/profile" style="color:var(--g2)">My Profile</a> to receive booking receipts by email.</span>`;
        notice.className='receipt-email-notice receipt-email-info';
      }
      notice.style.display='flex';
    }

    modal.classList.add('open'); document.body.style.overflow='hidden';
  }
}

/* ── CANCEL BOOKING — With Refund Modal ── */
function initCancelBooking() {
  const modal      = $('cancelModal');
  const closeBtn   = $('cancelModalClose');
  const confirmBtn = $('cancelConfirmBtn');
  if (!modal) return;

  let _cancelUrl = '';
  let _cancelId  = '';
  let _cancelRow = null;

  $$('.cancel-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      _cancelUrl = btn.dataset.url;
      _cancelId  = btn.dataset.id;
      _cancelRow = $('bk-' + _cancelId);

      const sub = $('cancelModalSubtitle');
      if (sub) sub.textContent = `${btn.dataset.cottage} · ${btn.dataset.date} · ₱${Number(btn.dataset.total||0).toLocaleString()}`;

      modal.classList.add('open');
      document.body.style.overflow = 'hidden';
      setTimeout(() => closeBtn?.focus(), 80);
    });
  });

  function closeModal() { modal.classList.remove('open'); document.body.style.overflow = ''; }

  closeBtn?.addEventListener('click', closeModal);
  modal?.addEventListener('click', e => { if (e.target === modal) closeModal(); });
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && modal.classList.contains('open')) closeModal(); });

  confirmBtn?.addEventListener('click', async () => {
    setBtn(confirmBtn, true);
    const { ok, data } = await api(_cancelUrl, {});
    setBtn(confirmBtn, false);
    if (ok && data.success) {
      const emailMsg = data.email_sent ? ' A cancellation & refund email has been sent to your inbox.' : '';
      toast('✅ Booking cancelled. Refund within 3–5 business days.' + emailMsg);
      closeModal();
      if (_cancelRow) {
        _cancelRow.classList.add('bk-row-cancelled');
        const badge = _cancelRow.querySelector('.bk-badge');
        if (badge) { badge.textContent = 'Cancelled'; badge.className = 'bk-badge bk-cancelled'; }
        _cancelRow.querySelector('.bk-actions')?.remove();
      }
    } else {
      toast('❌ ' + (data.message || 'Could not cancel.'), 'danger');
    }
  });
}

/* ── RESCHEDULE ── */
function initReschedule() {
  const modal=$('rescheduleModal'), closeBtn=$('rescheduleClose'), confirmBtn=$('rescheduleConfirm');
  let currentId=null;
  if (!modal) return;

  $$('.reschedule-btn').forEach(btn=>{
    btn.addEventListener('click',()=>{
      currentId=btn.dataset.id;
      const newDate=$('newDate'), newShift=$('newShift');
      if(newDate){ newDate.min=new Date().toISOString().split('T')[0]; newDate.value=btn.dataset.date||''; }
      if(newShift&&btn.dataset.shift) { newShift.value=btn.dataset.shift.includes('Night')?'Night Tour (6pm-12mn)':'Day Tour (8am-5pm)'; }
      if($('rescheduleTitle')) $('rescheduleTitle').textContent=`Current: ${btn.dataset.cottage} — ${btn.dataset.date}`;
      hideErr('rescheduleErr');
      modal.classList.add('open'); document.body.style.overflow='hidden';
      setTimeout(()=>newDate?.focus(),80);
    });
  });

  const closeModal=()=>{ modal.classList.remove('open'); document.body.style.overflow=''; };
  closeBtn?.addEventListener('click',closeModal);
  modal?.addEventListener('click', e=>{ if(e.target===modal) closeModal(); });
  document.addEventListener('keydown', e=>{ if(e.key==='Escape'&&modal.classList.contains('open')) closeModal(); });

  confirmBtn?.addEventListener('click', async()=>{
    const newDate=($('newDate')?.value||'').trim(), newShift=($('newShift')?.value||'').trim();
    if(!newDate){ showErr('rescheduleErr','⚠️ Please select a new date.'); return; }
    setBtn(confirmBtn,true);
    const {ok,data}=await api(window.RESCHEDULE_BASE+currentId,{date:newDate,shift:newShift});
    setBtn(confirmBtn,false);
    if(ok&&data.success){
      toast('✅ '+data.message); closeModal();
      const row=$('bk-'+currentId);
      if(row){
        const meta=row.querySelector('.bk-meta'); if(meta){ const spans=meta.querySelectorAll('span'); if(spans[0]) spans[0].textContent='📅 '+data.new_date; if(spans[1]) spans[1].textContent='🕐 '+(data.new_shift.includes('Night')?'Night Tour':'Day Tour'); }
        const total=row.querySelector('.bk-total'); if(total) total.textContent='₱'+Number(data.new_total).toLocaleString();
        const resBtn=row.querySelector('.reschedule-btn'); if(resBtn){resBtn.dataset.date=data.new_date;resBtn.dataset.shift=data.new_shift;}
      }
    } else showErr('rescheduleErr','❌ '+(data.message||'Reschedule failed.'));
  });
}

/* ── REVIEWS ── */
function initReviews() {
  const modal=$('reviewModal'), closeBtn=$('reviewClose'), confirmBtn=$('reviewConfirm');
  let currentId=null;
  if (!modal) return;

  $$('.review-btn').forEach(btn=>{
    btn.addEventListener('click',()=>{
      currentId=btn.dataset.id;
      if($('reviewTitle')) $('reviewTitle').textContent=`Reviewing: ${btn.dataset.cottage}`;
      if($('selectedRating')) $('selectedRating').value='0';
      if($('reviewComment')) $('reviewComment').value='';
      $$('.star-btn').forEach(s=>{s.textContent='☆';s.classList.remove('filled');});
      hideErr('reviewErr');
      modal.classList.add('open'); document.body.style.overflow='hidden';
    });
  });

  const closeModal=()=>{ modal.classList.remove('open'); document.body.style.overflow=''; };
  closeBtn?.addEventListener('click',closeModal);
  modal?.addEventListener('click', e=>{ if(e.target===modal) closeModal(); });
  document.addEventListener('keydown', e=>{ if(e.key==='Escape'&&modal.classList.contains('open')) closeModal(); });

  const stars=$$('.star-btn');
  stars.forEach((btn,i)=>{
    btn.addEventListener('click',()=>{
      if($('selectedRating')) $('selectedRating').value=String(i+1);
      stars.forEach((s,j)=>{ s.textContent=j<=i?'⭐':'☆'; s.classList.toggle('filled',j<=i); });
    });
    btn.addEventListener('mouseenter',()=>{ stars.forEach((s,j)=>{ s.textContent=j<=i?'⭐':'☆'; }); });
  });
  $('starPicker')?.addEventListener('mouseleave',()=>{
    const val=parseInt($('selectedRating')?.value||'0');
    stars.forEach((s,j)=>{ s.textContent=j<val?'⭐':'☆'; });
  });

  confirmBtn?.addEventListener('click', async()=>{
    const rating=parseInt($('selectedRating')?.value||'0'), comment=($('reviewComment')?.value||'').trim();
    if(!rating){ showErr('reviewErr','⚠️ Please select a star rating.'); return; }
    setBtn(confirmBtn,true);
    const {ok,data}=await api(window.REVIEW_BASE+currentId,{rating,comment});
    setBtn(confirmBtn,false);
    if(ok&&data.success){
      toast('✅ '+data.message); closeModal();
      const btn=document.querySelector(`.review-btn[data-id="${currentId}"]`);
      if(btn){ btn.replaceWith(Object.assign(document.createElement('span'),{textContent:'✅ Reviewed',style:'font-size:.75rem;color:var(--g2)'})); }
    } else showErr('reviewErr','❌ '+(data.message||'Could not submit review.'));
  });
}

/* ── PROFILE ── */
function initProfile() {
  const emailForm=$('emailForm'), pwForm=$('pwForm');
  if (!emailForm && !pwForm) return;

  [['eyeCurrent','currentPw'],['eyeNew','newPw']].forEach(([bid,pid])=>{
    $(bid)?.addEventListener('click',function(){const p=$(pid);if(!p)return;p.type=p.type==='password'?'text':'password';this.textContent=p.type==='text'?'🙈':'👁';this.setAttribute('aria-label',p.type==='text'?'Hide password':'Show password');});
  });

  emailForm?.addEventListener('submit', async e=>{
    e.preventDefault(); hideErr('emailErr');
    const email=($('emailInput')?.value||'').trim();
    const btn=$('emailBtn'); setBtn(btn,true);
    const {ok,data}=await api(window.PROFILE_URL,{action:'update_email',email});
    setBtn(btn,false);
    if(ok&&data.success) toast('✅ '+data.message); else showErr('emailErr','❌ '+(data.message||'Error.'));
  });

  pwForm?.addEventListener('submit', async e=>{
    e.preventDefault(); hideErr('pwErr');
    const current=($('currentPw')?.value||'').trim(), newPw=($('newPw')?.value||'').trim(), confirm=($('confirmPw')?.value||'').trim();
    if(!current){ showErr('pwErr','⚠️ Please enter your current password.'); return; }
    if(newPw.length<6){ showErr('pwErr','⚠️ New password must be at least 6 characters.'); return; }
    if(newPw!==confirm){ showErr('pwErr','⚠️ Passwords do not match.'); return; }
    const btn=$('pwBtn'); setBtn(btn,true);
    const {ok,data}=await api(window.PROFILE_URL,{action:'change_password',current,new_pw:newPw,confirm});
    setBtn(btn,false);
    if(ok&&data.success){toast('✅ '+data.message);pwForm.reset();} else showErr('pwErr','❌ '+(data.message||'Error.'));
  });
}

/* ── ADMIN: ADD COTTAGE (Fixed — updates inventory without reload) ── */
function initAddCottage() {
  const form=$('addCottageForm'); if(!form) return;
  const imgInput=$('imgInput'), imgPreview=$('imgPreview'), addErr=$('addErr'), zoneLabel=$('fileZoneLabel'), addBtn=$('addBtn');

  // Live image preview
  imgInput?.addEventListener('change',()=>{
    const file=imgInput.files[0]; if(!file) return;
    if(imgPreview){imgPreview.innerHTML=`<img src="${URL.createObjectURL(file)}" alt="Preview of selected image" style="width:100%;height:88px;object-fit:cover;border-radius:8px;display:block"/>`;} 
    if(zoneLabel) zoneLabel.textContent=`📷 ${file.name}`;
  });

  // Drag-and-drop support
  const zone=form.querySelector('.file-zone');
  zone?.addEventListener('dragover',e=>{e.preventDefault();zone.classList.add('drag-over');});
  zone?.addEventListener('dragleave',()=>zone.classList.remove('drag-over'));
  zone?.addEventListener('drop',e=>{
    e.preventDefault(); zone.classList.remove('drag-over');
    const file=e.dataTransfer.files[0];
    if(file&&imgInput){ const dt=new DataTransfer(); dt.items.add(file); imgInput.files=dt.files; imgInput.dispatchEvent(new Event('change')); }
  });

  form.addEventListener('submit', async e=>{
    e.preventDefault(); if(addErr) addErr.style.display='none';
    const name=(form.querySelector('[name="name"]')?.value||'').trim();
    const price=(form.querySelector('[name="price"]')?.value||'').trim();
    const inc=(form.querySelector('[name="inclusions"]')?.value||'').trim();
    if(!name||!price||!inc){ if(addErr){addErr.textContent='❌ All fields are required.';addErr.style.display='block';} return; }

    const csrfVal=($('addCsrf')?.value||csrf()); 
    const fd=new FormData(form); fd.set('csrf_token',csrfVal);
    if(addBtn){addBtn.disabled=true;addBtn.querySelector('.btn-label')&&(addBtn.querySelector('.btn-label').textContent='⏳ Saving…');}
    const {ok,data}=await apiForm(window.ADD_COTTAGE_URL,fd);
    if(addBtn){addBtn.disabled=false;if(addBtn.querySelector('.btn-label'))addBtn.querySelector('.btn-label').textContent='💾 Save Accommodation';}
    if(ok&&data.success){
      toast('✅ '+data.message);

      // ── Update inventory list immediately without page reload ──
      const invList=$('invList');
      if(invList){
        // Remove empty placeholder if present
        const empty=invList.querySelector('p');
        if(empty) empty.remove();

        const newId='new-'+Date.now();
        const imgSrc = data.image_fn
          ? `/static/images/${data.image_fn}`
          : `/static/images/welcome.jpg`;
        const row=document.createElement('div');
        row.className='inv-row'; row.id='inv-'+newId;
        row.innerHTML=`
          <img src="${imgSrc}" alt="${name}" onerror="this.src='/static/images/welcome.jpg'" style="width:50px;height:40px;object-fit:cover;border-radius:6px;flex-shrink:0;display:block"/>
          <div class="inv-info"><strong>${name}</strong><span>₱${Number(price).toLocaleString()} · No reviews</span></div>
          <div style="display:flex;gap:.4rem">
            <span class="btn btn-outline btn-sm" style="opacity:.5;cursor:default" title="Save to see edit/delete">Saved ✓</span>
          </div>`;
        invList.prepend(row);
        row.scrollIntoView({behavior:'smooth',block:'nearest'});
        row.style.animation='cardIn .4s ease both';

        // Update count badge
        const countBadge=document.querySelector('.a-count');
        if(countBadge){
          const cur=parseInt(countBadge.textContent)||0;
          countBadge.textContent=(cur+1)+' items';
        }
      }

      form.reset();
      if(imgPreview)imgPreview.innerHTML='';
      if(zoneLabel)zoneLabel.textContent='📂 Click to select or drag image here';

      // Reload after 3s so edit/delete buttons become active
      setTimeout(()=>location.reload(),3000);
    }
    else if(addErr){addErr.textContent='❌ '+(data.message||'Error.');addErr.style.display='block';}
  });
}

/* ── ADMIN: EDIT COTTAGE ── */
function initEditCottage() {
  const modal=$('editModal'), closeBtn=$('editClose'), form=$('editCottageForm');
  let editUrl='';
  if (!modal) return;

  // Preview in edit modal
  const editFileInput=form?.querySelector('input[type="file"]');
  const editPreviewWrap=form?.querySelector('.edit-img-preview');
  editFileInput?.addEventListener('change',()=>{
    const file=editFileInput.files[0]; if(!file||!editPreviewWrap) return;
    editPreviewWrap.innerHTML=`<img src="${URL.createObjectURL(file)}" alt="New photo preview" style="width:100%;height:80px;object-fit:cover;border-radius:8px;margin-top:.5rem;display:block"/>`;
  });

  $$('.edit-cottage').forEach(btn=>{
    btn.addEventListener('click',()=>{
      editUrl=btn.dataset.url;
      if($('editName'))   $('editName').value=btn.dataset.name||'';
      if($('editPrice'))  $('editPrice').value=btn.dataset.price||'';
      if($('editInc'))    $('editInc').value=btn.dataset.inc||'';
      if($('editMax'))    $('editMax').value=btn.dataset.max||'2';
      if($('editPolicy')) $('editPolicy').value=btn.dataset.policy||'';
      if(editPreviewWrap) editPreviewWrap.innerHTML='';
      hideErr('editErr');
      modal.classList.add('open'); document.body.style.overflow='hidden';
      setTimeout(()=>$('editName')?.focus(),80);
    });
  });

  const closeModal=()=>{ modal.classList.remove('open'); document.body.style.overflow=''; };
  closeBtn?.addEventListener('click',closeModal);
  modal?.addEventListener('click', e=>{ if(e.target===modal) closeModal(); });
  document.addEventListener('keydown', e=>{ if(e.key==='Escape'&&modal.classList.contains('open')) closeModal(); });

  form?.addEventListener('submit', async e=>{
    e.preventDefault(); hideErr('editErr');
    const csrfVal=($('editCsrf')?.value||csrf()); const fd=new FormData(form); fd.set('csrf_token',csrfVal);
    const submitBtn=form.querySelector('button[type="submit"]'); setBtn(submitBtn,true);
    const {ok,data}=await apiForm(editUrl,fd);
    setBtn(submitBtn,false);
    if(ok&&data.success){toast('✅ '+data.message);closeModal();setTimeout(()=>location.reload(),1200);}
    else showErr('editErr','❌ '+(data.message||'Update failed.'));
  });
}

/* ── ADMIN: DELETE COTTAGE ── */
function initDeleteCottage() {
  $$('.del-cottage').forEach(btn=>{
    btn.addEventListener('click', async()=>{
      const {id,name,url}=btn.dataset;
      if(!confirm(`Delete "${name}"?\n\nAll reservations will also be removed.`)) return;
      const orig=btn.textContent; btn.disabled=true; btn.textContent='⏳';
      const {ok,data}=await api(url,{});
      if(ok&&data.success){toast('✅ '+data.message);const row=$('inv-'+id);if(row){row.style.transition='opacity .3s,transform .3s';row.style.opacity='0';row.style.transform='translateX(16px)';setTimeout(()=>row.remove(),320);}}
      else{toast('❌ '+(data.message||'Delete failed.'),'danger');btn.disabled=false;btn.textContent=orig;}
    });
  });
}

/* ── ADMIN: DELETE USER ── */
function initDeleteUser() {
  $$('.del-user').forEach(btn=>{
    btn.addEventListener('click', async()=>{
      const {username,url}=btn.dataset;
      if(!confirm(`Remove guest "${username}"?`)) return;
      const orig=btn.textContent; btn.disabled=true; btn.textContent='⏳';
      const {ok,data}=await api(url,{});
      if(ok&&data.success){toast('✅ '+data.message);const row=$('gr-'+username);if(row){row.style.transition='opacity .3s';row.style.opacity='0';setTimeout(()=>row.remove(),320);}}
      else{toast('❌ '+(data.message||'Error.'),'danger');btn.disabled=false;btn.textContent=orig;}
    });
  });
}

/* ── ADMIN: CANCEL RESERVATION ── */
function initCancelReservation() {
  $$('.cancel-res-btn').forEach(btn=>{
    btn.addEventListener('click', async()=>{
      if(!confirm('Cancel reservation #'+btn.dataset.id+'?\n\nThe guest will be refunded.')) return;
      const orig=btn.textContent; btn.disabled=true; btn.textContent='⏳';
      const {ok,data}=await api(btn.dataset.url,{});
      if(ok&&data.success){
        toast('✅ '+data.message);
        [$('res-'+btn.dataset.id),$('res-all-'+btn.dataset.id)].forEach(row=>{
          if(row){const badge=row.querySelector('.badge');if(badge){badge.textContent='Cancelled';badge.className='badge cancelled';}btn.remove();}
        });
      } else{toast('❌ '+(data.message||'Error.'),'danger');btn.disabled=false;btn.textContent=orig;}
    });
  });
}

/* ── ADMIN: WALK-IN BOOKING ── */
function initWalkinBooking() {
  const toggleBtn=$('walkinToggle'), formWrap=$('walkinForm'), form=$('walkinBookingForm');
  if (!toggleBtn||!form) return;
  toggleBtn.addEventListener('click',()=>{
    const hidden=formWrap.style.display==='none'; formWrap.style.display=hidden?'block':'none'; toggleBtn.textContent=hidden?'✕ Close':'+ New Walk-in';
    const dateInput=form.querySelector('input[type="date"]'); if(dateInput) dateInput.min=new Date().toISOString().split('T')[0];
    toggleBtn.setAttribute('aria-expanded',String(hidden));
    if(hidden) form.querySelector('input,select')?.focus();
  });
  form.addEventListener('submit', async e=>{
    e.preventDefault(); hideErr('walkinErr');
    const csrfVal=($('walkinCsrf')?.value||csrf()); const fd=new FormData(form);
    const body={}; fd.forEach((v,k)=>body[k]=v); body.csrf_token=csrfVal;
    const btn=$('walkinSubmit'); setBtn(btn,true);
    const {ok,data}=await api(window.WALKIN_URL,body);
    setBtn(btn,false);
    if(ok&&data.success){toast(`✅ Walk-in booking #${data.id} created! Total: ₱${Number(data.total).toLocaleString()}`);form.reset();formWrap.style.display='none';toggleBtn.textContent='+ New Walk-in';toggleBtn.setAttribute('aria-expanded','false');setTimeout(()=>location.reload(),1500);}
    else if($('walkinErr')){$('walkinErr').textContent='❌ '+(data.message||'Error.');$('walkinErr').style.display='block';}
  });
}

/* ── ADMIN: NOTIFICATIONS ── */
function initNotifications() {
  const bell=$('notifBtn'), panel=$('notifPanel'), markBtn=$('markReadBtn'), badge=$('notifBadge');
  if (!bell) return;
  bell.addEventListener('click', e=>{ e.stopPropagation(); const open=panel.style.display==='flex'; panel.style.display=open?'none':'flex'; panel.style.flexDirection='column'; bell.setAttribute('aria-expanded',String(!open)); if(!open) markAllRead(); });
  document.addEventListener('click', e=>{ if(!bell.contains(e.target)&&!panel?.contains(e.target)) { if(panel) panel.style.display='none'; bell.setAttribute('aria-expanded','false'); } });
  async function markAllRead() { await api(window.NOTIF_READ_URL,{}); if(badge) badge.style.display='none'; $$('.notif-unread').forEach(el=>el.classList.remove('notif-unread')); }
  markBtn?.addEventListener('click', async e=>{ e.stopPropagation(); await markAllRead(); toast('All notifications marked as read.'); });
  async function pollNotifs() { try { const r=await fetch(window.NOTIF_URL); const d=await r.json(); if(badge){ if(d.count>0){badge.textContent=d.count;badge.style.display='flex';}else{badge.style.display='none';} } } catch {} }
  if (window.NOTIF_URL) setInterval(pollNotifs, 30000);
}

/* ── SCROLL REVEAL ── */
function initScrollReveal() {
  if(!('IntersectionObserver' in window)||window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  const obs=new IntersectionObserver(entries=>{entries.forEach(e=>{if(e.isIntersecting){e.target.style.animation='cardIn .45s ease forwards';obs.unobserve(e.target);}});},{threshold:.08});
  $$('.c-card,.stat-card,.bk-row,.feature-card,.contact-card').forEach(el=>{el.style.opacity='0';obs.observe(el);});
}

/* ── SORT ACCOMMODATIONS ── */
function initSort() {
  const sortSel=$('sortSelect');
  if(!sortSel) return;
  sortSel.addEventListener('change',()=>{
    const val=sortSel.value;
    const grid=$('cottageGrid');
    if(!grid) return;
    const cards=[...$$('.c-card')];
    cards.sort((a,b)=>{
      const pa=parseFloat(a.dataset.price)||0, pb=parseFloat(b.dataset.price)||0;
      const na=(a.dataset.name||''), nb=(b.dataset.name||'');
      if(val==='price-asc') return pa-pb;
      if(val==='price-desc') return pb-pa;
      if(val==='name-asc') return na.localeCompare(nb);
      return 0;
    });
    cards.forEach(c=>grid.appendChild(c));
  });
}

/* ── INIT ALL ── */
document.addEventListener('DOMContentLoaded', () => {
  initDarkMode();
  initSidebar();
  initParticles();
  initAdminTabs();
  initAuthPage();
  initDashboardFilter();
  initSort();
  initAvailabilityChecker();
  initBookingCalendar();
  initBookingPage();
  initCancelBooking();
  initReschedule();
  initReviews();
  initProfile();
  initAddCottage();
  initEditCottage();
  initDeleteCottage();
  initDeleteUser();
  initCancelReservation();
  initWalkinBooking();
  initNotifications();
  initScrollReveal();
});

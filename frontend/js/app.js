const categories = {'':'Tất cả','dien-thoai':'Điện thoại','laptop':'Laptop','tai-nghe':'Tai nghe','dong-ho':'Đồng hồ','phu-kien':'Phụ kiện'};
const money = n => new Intl.NumberFormat('vi-VN',{style:'currency',currency:'VND'}).format(n);
const esc = s => String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const $ = s => document.querySelector(s);
const user = new URLSearchParams(location.search).get('user') || 'demo';
const cartPath = '/cart/' + encodeURIComponent(user);
const icons = {plus:'<path d="M12 5v14M5 12h14"/>',bag:'<path d="M5 7h14l1 14H4L5 7Z"/><path d="M9 8V6a3 3 0 0 1 6 0v2"/>'};
const icon = name => '<svg viewBox="0 0 24 24" aria-hidden="true">'+icons[name]+'</svg>';
let selected='', query='', requestId=0, busy=false, cartData=null, timer;
const image = p => /^\/assets\/images\/products\/SP[0-9]{3}\.webp$/.test(p.image||'') ? p.image : '/assets/phu-kien.svg';
function setupImages(root){root.querySelectorAll('img').forEach(img=>{img.addEventListener('error',()=>{img.src='/assets/phu-kien.svg';img.alt='Không tải được ảnh '+img.alt;img.classList.add('image-error');const note=document.createElement('span');note.className='image-error-note';note.textContent='Ảnh tạm thời không khả dụng';img.parentElement.append(note);},{once:true});});}
function message(text,error=false){clearTimeout(timer);$('#message').textContent=text;$('#message').className=error?'error':'';if(text&&!error)timer=setTimeout(()=>{$('#message').textContent='';},4500);}
async function api(path, options={}){
  const controller=new AbortController(), timeout=setTimeout(()=>controller.abort(),15000);
  try {
    const r=await fetch('/api'+path,{...options,signal:controller.signal,headers:{'Content-Type':'application/json'}});
    const data=await r.json();
    if(!r.ok)throw Error(typeof data.detail==='string'?data.detail:'Dữ liệu chưa hợp lệ. Vui lòng thử lại.');
    return data;
  } catch(e){if(e.name==='AbortError')throw Error('Kết nối quá lâu. Vui lòng thử lại.');throw e;}
  finally{clearTimeout(timeout);}
}
function setBusy(value){
 busy=value;$('#cart-view').classList.toggle('busy',value);$('#cart-items').setAttribute('aria-busy',String(value));
 $('#checkout-open').disabled=value||!cartData||!cartData.items.length;
 document.querySelectorAll('[data-add],[data-q],[data-remove],#clear').forEach(b=>{b.disabled=value||b.dataset.unavailable==='true'||b.dataset.limit==='true'||(b.id==='clear'&&(!cartData||!cartData.items.length));});
}
function empty(title,detail){return '<div class="empty-state">'+icon('bag')+'<h2>'+esc(title)+'</h2><p>'+esc(detail)+'</p></div>';}
async function products(){
 const id=++requestId, category=selected;
 $('#products').setAttribute('aria-busy','true');
 $('#products').innerHTML=Array.from({length:4},()=>'<div class="skeleton" aria-hidden="true"></div>').join('');
 $('#result-count').textContent='Đang tải…';
 try{
   const data=await api('/products'+(category?'?category='+encodeURIComponent(category):''));
   if(id!==requestId)return;
   const normalized=query.normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/đ/g,'d').toLowerCase();
   const filtered=data.filter(p=>(p.name+' '+p.description).normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/đ/g,'d').toLowerCase().includes(normalized));
   $('#catalog-title').textContent=query?'Kết quả tìm kiếm':(categories[category]||'Tất cả')+(category?'':' sản phẩm');
   $('#result-count').textContent=filtered.length+' sản phẩm';
   $('#products').innerHTML=filtered.length?filtered.map(p=>`<article class="product"><a href="#product/${encodeURIComponent(p.product_id)}" class="product-image"><img src="${image(p)}" width="320" height="240" alt="${esc(p.name)}" loading="lazy"></a><div class="product-body"><small>${esc(categories[p.category]||p.category)}</small><h3><a href="#product/${encodeURIComponent(p.product_id)}">${esc(p.name)}</a></h3><p class="price">${money(p.price_vnd)}</p><span class="stock ${p.stock<=0?'out':''}">${p.stock>0?'Còn '+p.stock+' sản phẩm':'Hết hàng'}</span><button class="add-button" data-add="${esc(p.product_id)}" data-unavailable="false" ${busy?'disabled':''} aria-label="Thêm ${esc(p.name)} vào giỏ">${icon('plus')}Thêm vào giỏ</button></div></article>`).join(''):empty('Chưa tìm thấy sản phẩm','Thử từ khóa khác hoặc chọn danh mục phù hợp.');
   setupImages($('#products'));
 }catch(e){if(id!==requestId)return;$('#products').innerHTML=empty('Không tải được sản phẩm','Kiểm tra kết nối và chọn Tải lại để thử lần nữa.');$('#result-count').textContent='';message(e.message,true);}
 finally{if(id===requestId)$('#products').setAttribute('aria-busy','false');}
}
function renderCart(d){
 cartData=d;
 $('#count').textContent=d.total_quantity;
 $('.cart-link').setAttribute('aria-label','Giỏ hàng, '+d.total_quantity+' sản phẩm');
 $('#cart-description').textContent=d.items.length+' loại sản phẩm';
 $('#summary-quantity').textContent=d.total_quantity;
 $('#subtotal').textContent=money(d.total_vnd);
 $('#total').textContent=money(d.total_vnd);
 $('#cart-items').innerHTML=d.items.length?d.items.map(p=>`<article class="cart-item"><img src="${image(p)}" alt="${esc(p.name)}" width="96" height="104"><div><small>${esc(categories[p.category]||p.product_id)}</small><h3>${esc(p.name)}</h3><span class="unit-price">${money(p.price_vnd)}</span><div class="row"><div class="quantity"><button data-id="${esc(p.product_id)}" data-q="${p.quantity-1}" aria-label="Giảm số lượng ${esc(p.name)}">−</button><span aria-label="Số lượng">${p.quantity}</span><button data-id="${esc(p.product_id)}" data-q="${p.quantity+1}" data-limit="${p.quantity>=99}" ${p.quantity>=99?'disabled':''} aria-label="Tăng số lượng ${esc(p.name)}">+</button></div><button class="remove" data-remove="${esc(p.product_id)}" aria-label="Xóa ${esc(p.name)} khỏi giỏ">Xóa</button></div></div><strong class="line-total">${money(p.subtotal_vnd)}</strong></article>`).join(''):empty('Giỏ hàng của bạn đang trống','Khám phá sản phẩm và thêm lựa chọn phù hợp vào giỏ.')+'<a class="empty-shopping button secondary-button" href="#catalog">Khám phá sản phẩm →</a>';
 setupImages($('#cart-items'));setBusy(busy);
}
async function loadCart(){
 $('#cart-items').setAttribute('aria-busy','true');
 try{renderCart(await api(cartPath));}
 catch(e){cartData=null;$('#cart-items').innerHTML=empty('Không tải được giỏ hàng','Chọn Tải lại để kiểm tra kết nối.');$('#clear').disabled=true;$('#checkout-open').disabled=true;message(e.message,true);}
 finally{$('#cart-items').setAttribute('aria-busy','false');}
}
async function mutate(path,method,body){
 if(busy)return;
 setBusy(true);
 try{renderCart(await api(cartPath+path,{method,body:body?JSON.stringify(body):undefined}));message('Đã cập nhật giỏ hàng.');}
 catch(e){message(e.message,true);}
 finally{setBusy(false);}
}
function route(){
 const hash=location.hash, inCart=hash==='#cart', inDetail=hash.startsWith('#product/'), inCheckout=hash==='#checkout', inOrder=hash.startsWith('#order/');
 $('#catalog-view').hidden=inCart||inDetail||inCheckout||inOrder;$('#cart-view').hidden=!inCart;
 $('#detail-view').hidden=!inDetail;$('#checkout-view').hidden=!inCheckout;$('#order-view').hidden=!inOrder;
 document.title=inCart?'Giỏ hàng — RedisCart':inDetail?'Chi tiết sản phẩm — RedisCart':inCheckout?'Xác nhận mua hàng — RedisCart':'RedisCart';
 if(inCart)loadCart();
 if(inDetail)loadDetail(decodeURIComponent(hash.slice(9)));
 if(inCheckout)prepareCheckout();
 if(inOrder)loadOrder(hash.slice(7));
}
$('#filters').innerHTML=Object.entries(categories).map(([k,v])=>`<button data-category="${k}" aria-pressed="${!k}" class="${!k?'active':''}">${v}</button>`).join('');
$('#filters').onclick=e=>{const b=e.target.closest('[data-category]');if(!b)return;selected=b.dataset.category;$('#filters').querySelectorAll('button').forEach(x=>{x.classList.toggle('active',x===b);x.setAttribute('aria-pressed',String(x===b));});products();};
let searchTimer;
$('#search').addEventListener('input',()=>{clearTimeout(searchTimer);query=$('#search').value.trim();searchTimer=setTimeout(products,250);});
$('#search-form').onsubmit=e=>{e.preventDefault();clearTimeout(searchTimer);query=$('#search').value.trim();location.hash='catalog';products();};
$('#products').onclick=e=>{const b=e.target.closest('[data-add]');if(b)mutate('/items','POST',{product_id:b.dataset.add,quantity:1});};
$('#cart-items').onclick=e=>{const b=e.target.closest('button');if(!b)return;if(b.dataset.remove)mutate('/items/'+encodeURIComponent(b.dataset.remove),'DELETE');else if(b.dataset.id)mutate('/items/'+encodeURIComponent(b.dataset.id),'PATCH',{quantity:Number(b.dataset.q)});};
$('#clear').onclick=()=>$('#clear-dialog').showModal();
$('#cancel-clear').onclick=()=>$('#clear-dialog').close();
$('#confirm-clear').onclick=()=>{$('#clear-dialog').close();mutate('','DELETE');};
$('#retry').onclick=()=>{message('');products();loadCart();};
window.addEventListener('hashchange',()=>{route();window.scrollTo({top:0,behavior:'instant'});if(location.hash==='#cart')$('#cart-heading').focus({preventScroll:true});});

const pendingStorage='rediscart.checkout.'+user;
let checkoutKey='', checkoutBusy=false, detailId=0;
function readPending(){try{return localStorage.getItem(pendingStorage)||'';}catch{return checkoutKey;}}
function clearPending(){checkoutKey='';try{localStorage.removeItem(pendingStorage);}catch{}}
async function loadDetail(pid){
 const id=++detailId;$('#detail-content').innerHTML='<p>Đang tải chi tiết sản phẩm…</p>';
 try{
 const p=await api('/products/'+encodeURIComponent(pid));if(id!==detailId)return;
 $('#detail-content').innerHTML=`<div class="detail-image"><img src="${image(p)}" alt="${esc(p.name)}"></div><div class="detail-info"><p class="eyebrow">${esc(categories[p.category]||p.category)}</p><h1>${esc(p.name)}</h1><p class="muted">Mã sản phẩm: ${esc(p.product_id)}</p><p class="detail-price">${money(p.price_vnd)}</p><p>${esc(p.description.replace(/\s*Dữ liệu mẫu đồ án\.?/gi,"").trim())}</p><p>Còn ${p.stock} sản phẩm</p>${specifications(p)}<form id="detail-form"><label for="detail-quantity">Số lượng</label><input id="detail-quantity" type="number" min="1" max="99" step="1" value="1" required><button class="primary" type="submit">Thêm vào giỏ hàng</button></form><a class="button secondary-button" href="#cart">Xem giỏ hàng →</a></div>`;
 setupImages($('#detail-content'));
 $('#detail-form').onsubmit=async e=>{e.preventDefault();const q=Number($('#detail-quantity').value);if(!Number.isInteger(q)||q<1||q>99){message('Số lượng từ 1 đến 99.',true);return;}const b=e.submitter;b.disabled=true;try{await mutate('/items','POST',{product_id:p.product_id,quantity:q});}finally{b.disabled=false;}};
 }catch(e){if(id===detailId)$('#detail-content').innerHTML=empty('Không tải được sản phẩm',e.message);}
}
function orderLines(items){return items.map(i=>`<div class="review-item"><div><strong>${esc(i.product_name||i.name)}</strong><p>${i.quantity} × ${money(i.unit_price_vnd??i.price_vnd)}</p></div><strong>${money(i.subtotal_vnd)}</strong></div>`).join('');}
async function prepareCheckout(){
 $('#checkout-confirm').disabled=true;$('#checkout-review').textContent='Đang tải giỏ hàng…';
 checkoutKey=readPending();
 try{
 const d=await api(cartPath);
 $('#checkout-review').innerHTML=d.items.length?orderLines(d.items)+`<div class="review-total">Tổng tiền <strong>${money(d.total_vnd)}</strong></div>`:empty('Giỏ hàng đang trống',checkoutKey?'Có yêu cầu chưa rõ kết quả. Chọn kiểm tra lại bên dưới.':'Quay lại mua sắm để thêm sản phẩm.');
 $('#checkout-confirm').textContent=checkoutKey?'Kiểm tra lại yêu cầu đã gửi':'Xác nhận mua hàng';
 $('#checkout-confirm').disabled=!d.items.length&&!checkoutKey;
 }catch(e){message(e.message,true);}
}
$('#checkout-open').onclick=()=>{location.hash='checkout';};
$('#checkout-confirm').onclick=async()=>{
 if(checkoutBusy)return;checkoutBusy=true;$('#checkout-confirm').disabled=true;
 try{
 if(!checkoutKey){
   checkoutKey=crypto.randomUUID();
   // Lưu trước khi gửi để reload/mất kết nối vẫn dùng lại mã cũ.
   try{localStorage.setItem(pendingStorage,checkoutKey);}catch{throw Error('Không lưu được mã giao dịch. Hãy bật lưu trữ trình duyệt rồi thử lại.');}
 }
 const result=await api(cartPath+'/checkout',{method:'POST',body:JSON.stringify({confirmed:true,idempotency_key:checkoutKey})});
 clearPending();location.hash='order/'+result.order_id;loadCart();products();
 }catch(e){message(e.message+' Yêu cầu chưa được xác nhận thành công; có thể kiểm tra lại bằng cùng mã.',true);}
 finally{checkoutBusy=false;$('#checkout-confirm').disabled=false;}
};
async function loadOrder(id){
 $('#order-content').textContent='Đang tải đơn hàng…';
 try{const o=await api(cartPath+'/orders/'+encodeURIComponent(id));
 $('#order-content').innerHTML=`<div class="success-mark" aria-hidden="true">✓</div><h1>Xác nhận mua hàng thành công</h1><p class="checkout-notice">Đơn hàng đã được xác nhận. Không thu tiền trực tuyến.</p><dl class="order-meta"><div><dt>Mã đơn hàng</dt><dd>${esc(o.order_id)}</dd></div><div><dt>Thời gian xác nhận</dt><dd>${esc(new Date(o.created_at).toLocaleString('vi-VN'))}</dd></div><div><dt>Trạng thái</dt><dd>Đã xác nhận</dd></div></dl>${orderLines(o.items)}<div class="review-total">Tổng tiền <strong>${money(o.total_vnd)}</strong></div><a href="#catalog" class="button primary">Quay lại mua sắm</a>`;
 }catch(e){$('#order-content').innerHTML=empty('Không tải được đơn hàng',e.message);}
}

const specLabels={screen:'Màn hình',storage:'Bộ nhớ',ram:'RAM',connectivity:'Kết nối',main_camera:'Camera chính',battery:'Pin',charging:'Sạc',chip:'Chip',screen_class:'Kích thước màn hình',model_family:'Dòng sản phẩm',usage:'Nhu cầu',panel:'Tấm nền',series:'Dòng máy',sku:'Mã SKU',connection:'Kết nối',design:'Thiết kế',noise_control:'Chống ồn',type:'Loại sản phẩm',case:'Kích thước vỏ',generation:'Thế hệ',body:'Khung',weight:'Khối lượng',water_resistance:'Chống nước',feature:'Tính năng',max_power:'Công suất tối đa',ports:'Số cổng',hdmi:'HDMI'};
function specifications(p){
 const specs=p.specs&&typeof p.specs==='object'?p.specs:{};
 const rows=Object.entries(specs).map(([key,value])=>'<div><dt>'+esc(specLabels[key]||key)+'</dt><dd>'+esc(value)+'</dd></div>').join('');
 const source=/^https:\/\//.test(p.manufacturer_url||'')?'<a class="manufacturer-link" target="_blank" rel="noopener noreferrer" href="'+esc(p.manufacturer_url)+'">Thông tin từ '+esc(p.brand||'nhà sản xuất')+' ↗</a>':'';
 return (rows?'<section class="specifications"><h2>Thông số sản phẩm</h2><dl>'+rows+'</dl></section>':'')+source;
}

route();products();if(location.hash!=='#cart')loadCart();



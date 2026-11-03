const {test} = require('node:test')
const assert = require('node:assert/strict')
const {readFileSync} = require('node:fs')
const vm = require('node:vm')
const React = require('react')
const {renderToStaticMarkup} = require('react-dom/server')
const swc = require('next/dist/build/swc')

async function component({fake=true, captureResult={purchase_id:'purchase-1'}, createResult={id:'FAKE-order-1'}, hooks=false}={}) {
  await swc.loadBindings()
  const source = readFileSync(require.resolve('../components/pages/events/PayPalSection.jsx'),'utf8')
  const code = swc.transformSync(source,{filename:'PayPalSection.jsx',jsc:{parser:{syntax:'ecmascript',jsx:true},transform:{react:{runtime:'automatic'}}},module:{type:'commonjs'}}).code
  const calls = [], state = []
  const sdk = {PayPalScriptProvider:({children}) => {
    assert.equal(fake,false,'Fake checkout mounted the remote PayPal SDK provider')
    return React.createElement('section',{'data-hosted-paypal':true},children)
  },PayPalButtons:() => React.createElement('button',null,'Hosted PayPal')}
  const mocks = {
    '@/config/paypal':{initialOptions:fake ? null : {'client-id':'fake-sandbox-client'},isFakePayment:fake},
    '@paypal/react-paypal-js':sdk,
    '@/services/paypal':{createOrder:async payload => {calls.push(['create',payload]);return createResult},onApprove:async id => {calls.push(['capture',id]);return captureResult}},
    sonner:{toast:{error:()=>{}}},
    '@/components/pages/modals/PayPalModal':{PaymentSuccessDialog:()=>null},
    'lucide-react':{Loader2:()=>null,AlertCircle:()=>null},
    '@/config/firebase':{analytics:null},'firebase/analytics':{logEvent:()=>{}},
    '@/config/events-utils':{resolvePurchaseMode:()=> 'public'},
  }
  if (hooks) mocks.react = {...React,useMemo:fn=>fn(),useState:initial=>{
    const index=state.length;state.push(initial);return [initial,value=>{state[index]=value}]
  }}
  const loaded = {exports:{}}
  vm.runInNewContext(code,{module:loaded,exports:loaded.exports,require:name=>name in mocks ? mocks[name] : require(name),console:{error(){}}})
  return {Component:loaded.exports.PayPalSection,calls,state}
}

const props = {event:{id:'evt-1'},cart:{total:12},purchaseMode:'public'}
function button(node) {
  if (!node || typeof node !== 'object') return undefined
  if (node.type === 'button') return node
  for (const child of [node.props?.children].flat(Infinity)) {
    const found=button(child);if(found)return found
  }
}

test('fake checkout renders without mounting hosted PayPal SDK',async()=>{
  const {Component,calls}=await component()
  const html=renderToStaticMarkup(React.createElement(Component,props))
  assert.match(html,/pagamento simulato/i)
  assert.doesNotMatch(html,/data-hosted-paypal/)
  assert.deepEqual(calls,[])
})

test('fake approval uses existing create and capture callbacks',async()=>{
  const {Component,calls,state}=await component({hooks:true})
  const submit=button(Component(props))
  assert.ok(submit,'A local payment button is required')
  await submit.props.onClick()
  assert.equal(calls.length,2)
  assert.equal(calls[0][0],'create')
  assert.deepEqual(JSON.parse(JSON.stringify(calls[0][1])),{cart:props.cart})
  assert.deepEqual(calls[1],['capture','FAKE-order-1'])
  assert.equal(state[0],true)
  assert.equal(state[3],true)
})

test('fake checkout preserves disabled state',async()=>{
  const {Component}=await component({hooks:true})
  assert.equal(button(Component({...props,disabled:true}))?.props.disabled,true)
})

test('failed local order never reaches capture',async()=>{
  const {Component,calls,state}=await component({hooks:true,createResult:{error:'invalid_cart'}})
  const submit=button(Component(props))
  assert.ok(submit)
  await submit.props.onClick()
  assert.equal(calls.length,1)
  assert.equal(state[0],false)
})

test('sandbox checkout retains hosted buttons',async()=>{
  const {Component}=await component({fake:false})
  const html=renderToStaticMarkup(React.createElement(Component,props))
  assert.match(html,/Hosted PayPal/)
  assert.doesNotMatch(html,/pagamento simulato/i)
})

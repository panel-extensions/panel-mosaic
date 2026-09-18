import {InstantiateContext, astToDOM, parseSpec} from "@uwdata/mosaic-spec"
import {tableFromIPC} from "@uwdata/flechette"

function decodeBase64(b64) {
  const binary = atob(b64)
  const bytes = new Uint8Array(binary.length)
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i)
  }
  return bytes
}

function isSelection(param) {
  return typeof param?.predicate === "function"
}

function jsonSafe(value) {
  try {
    return JSON.parse(JSON.stringify(value ?? null))
  } catch {
    return null
  }
}

function predicateSQL(selection) {
  const predicate = selection.predicate(undefined) ?? []
  const parts = (Array.isArray(predicate) ? predicate : [predicate]).map(String)
  return parts.length > 1 ? parts.map((part) => `(${part})`).join(" AND ") : parts[0] ?? ""
}

export function render({model, el}) {
  el.classList.add("mosaic-pane")

  // Each pane has an independent context so multiple panes on a page do not
  // replace one another's database connector.
  const ctx = new InstantiateContext()
  const {coordinator} = ctx
  const pending = new Map()
  let counter = 0

  coordinator.databaseConnector({
    query(query) {
      return new Promise((resolve, reject) => {
        const uuid = `${++counter}`
        pending.set(uuid, {resolve, reject})
        model.send_msg({...query, uuid})
      })
    },
  })

  model.on("msg:custom", (msg) => {
    const query = pending.get(msg.uuid)
    if (query === undefined) {
      return
    }
    pending.delete(msg.uuid)
    if (msg.error) {
      model.ready = false
      model.error = msg.error
      query.reject(new Error(msg.error))
    } else if (msg.type === "arrow") {
      query.resolve(tableFromIPC(decodeBase64(msg.data), {useDate: true}))
    } else if (msg.type === "json") {
      query.resolve(msg.result)
    } else {
      query.resolve({})
    }
  })

  let applied = null

  async function updateSpec() {
    const spec = model.spec
    const json = JSON.stringify(spec)
    if (json === applied) {
      return
    }
    applied = json
    model.ready = false
    model.error = ""
    coordinator.clear()
    if (spec == null || Object.keys(spec).length === 0) {
      el.replaceChildren()
      return
    }

    try {
      const dom = await astToDOM(parseSpec(spec), {api: ctx.api})
      el.replaceChildren(dom.element)

      let params = {}
      const snapshot = (param, value) => ({
        value: jsonSafe(value),
        ...(isSelection(param) ? {predicate: predicateSQL(param)} : {}),
      })
      const publish = () => {
        model.params = params
      }
      for (const [name, param] of dom.params) {
        params[name] = snapshot(param, param.value)
        param.addEventListener("value", (value) => {
          params = {...params, [name]: snapshot(param, value)}
          publish()
        })
      }
      publish()
      model.ready = true
    } catch (error) {
      model.ready = false
      model.error = String(error.message ?? error)
      const paneError = document.createElement("pre")
      paneError.className = "mosaic-pane-error"
      paneError.textContent = `Could not render Mosaic spec:\n${error.message ?? error}`
      el.replaceChildren(paneError)
    }
  }

  function configureCoordinator() {
    if (model.preagg_schema) {
      coordinator.preaggregator.schema = model.preagg_schema
    }
  }

  model.on("spec", () => updateSpec())
  model.on("preagg_schema", () => configureCoordinator())
  configureCoordinator()
  updateSpec()

  return () => coordinator.clear()
}

export default {render}

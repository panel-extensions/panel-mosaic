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
  let dashboard = null
  let resizeFrame = null
  let fitting = false
  let fitAgain = false

  function dashboardBounds(root) {
    const selector = ".plot > svg, .legend, [id^='table-'], select, input"
    const nodes = [...root.querySelectorAll(selector)]
    const rects = nodes
      .map((node) => node.getBoundingClientRect())
      .filter((rect) => rect.width > 0 && rect.height > 0)
    if (rects.length === 0) {
      return null
    }
    return {
      width: Math.max(...rects.map((rect) => rect.right))
        - Math.min(...rects.map((rect) => rect.left)),
      height: Math.max(...rects.map((rect) => rect.bottom))
        - Math.min(...rects.map((rect) => rect.top)),
    }
  }

  function plotElements(root) {
    return [
      ...(root.matches?.(".plot") ? [root] : []),
      ...root.querySelectorAll(".plot"),
    ]
  }

  function scheduleFit() {
    if (!dashboard || !model.responsive) {
      return
    }
    if (fitting) {
      fitAgain = true
      return
    }
    cancelAnimationFrame(resizeFrame)
    resizeFrame = requestAnimationFrame(() => fitDashboard())
  }

  async function fitDashboard(pass = 0) {
    const root = dashboard?.element
    if (!root || !root.isConnected) {
      return
    }
    if (fitting) {
      fitAgain = true
      return
    }

    fitting = true
    try {
      const available = el.getBoundingClientRect()
      const content = dashboardBounds(root)
      if (!content || available.width <= 0 || available.height <= 0) {
        return
      }

      const widthRatio = available.width / content.width
      const heightRatio = available.height / content.height
      if (Math.abs(widthRatio - 1) < 0.02 && Math.abs(heightRatio - 1) < 0.02) {
        return
      }

      const updates = []
      for (const element of plotElements(root)) {
        const plot = element.value
        if (!plot?.getAttribute || !plot?.setAttribute || !plot?.update) {
          continue
        }
        const width = plot.getAttribute("width")
        const height = plot.getAttribute("height")
        let changed = false
        if (Number.isFinite(width)) {
          const next = Math.min(
            4 * available.width,
            Math.max(160, Math.round(width * Math.max(0.25, Math.min(4, widthRatio))))
          )
          changed = plot.setAttribute("width", next, {silent: true}) || changed
        }
        if (Number.isFinite(height)) {
          const next = Math.min(
            4 * available.height,
            Math.max(120, Math.round(height * Math.max(0.25, Math.min(4, heightRatio))))
          )
          changed = plot.setAttribute("height", next, {silent: true}) || changed
        }
        if (changed) {
          updates.push(plot.update())
        }
      }
      await Promise.allSettled(updates)
      if (updates.length > 0 && pass < 2) {
        await new Promise((resolve) => requestAnimationFrame(resolve))
        fitting = false
        await fitDashboard(pass + 1)
      }
    } finally {
      fitting = false
      if (fitAgain) {
        fitAgain = false
        scheduleFit()
      }
    }
  }

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
      dashboard = dom
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
      scheduleFit()
    } catch (error) {
      dashboard = null
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
  model.on("responsive", () => scheduleFit())
  const resizeObserver = new ResizeObserver(() => scheduleFit())
  resizeObserver.observe(el)
  configureCoordinator()
  updateSpec()

  return () => {
    resizeObserver.disconnect()
    cancelAnimationFrame(resizeFrame)
    coordinator.clear()
  }
}

export default {render}

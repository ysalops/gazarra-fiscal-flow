const API = "http://localhost:8001/api";

const AUTH_TOKEN_KEY = "gazarra_access_token";
let currentUser = null;
let adminInitialized = false;
let adminSelectedUserId = null;
let fiscalCompaniesCache = [];
let companySearchTimer = null;

const nativeFetch = window.fetch.bind(window);
window.fetch = async (input, init = {}) => {
  const url = typeof input === "string" ? input : input.url;
  const token = localStorage.getItem(AUTH_TOKEN_KEY);
  const options = { ...init };
  const headers = new Headers(init.headers || (typeof input !== "string" ? input.headers : undefined));

  if (token && url.startsWith(API) && !url.includes("/auth/login")) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  options.headers = headers;

  const response = await nativeFetch(input, options);
  if (response.status === 401 && !url.includes("/auth/login") && token) {
    localStorage.removeItem(AUTH_TOKEN_KEY);
    showLoginScreen("Sua sessão expirou. Entre novamente.");
  }
  return response;
};

function showLoginScreen(message = "") {
  document.body.classList.add("auth-locked");
  document.getElementById("loginScreen")?.classList.remove("hidden");
  const box = document.getElementById("loginMessage");
  if (box) {
    box.textContent = message;
    box.classList.toggle("hidden", !message);
  }
}

function hideLoginScreen() {
  document.body.classList.remove("auth-locked");
  document.getElementById("loginScreen")?.classList.add("hidden");
  restartViewAnimations(document.querySelector(".view.active-view"));
}

function updateUserUI(user) {
  currentUser = user;
  const name = document.getElementById("sidebarUserName");
  const role = document.getElementById("sidebarUserRole");
  const avatar = document.getElementById("sidebarUserAvatar");
  if (name) name.textContent = user.name;
  if (role) role.textContent = user.role === "admin" ? "Administrador" : "Analista";
  if (avatar) avatar.textContent = (user.name || "G").trim().charAt(0).toUpperCase();

  document.querySelectorAll(".admin-only").forEach((element) => {
    element.classList.toggle("hidden", user.role !== "admin");
  });
}

async function bootstrapAccessibleContext() {
  try {
    const response = await fetch(`${API}/fiscal/companies`);
    const companies = await response.json();
    if (!response.ok || !companies.length) return;

    fiscalCompaniesCache = companies;
    const currentAllowed = companies.find(
      (company) => Number(company.id) === Number(appContext.companyId)
    );
    const selected = currentAllowed || companies[0];
    updateAppContext({
      companyId: selected.id,
      companyName: selected.name,
      competence: null
    });

    const count = document.getElementById("dashboardCompaniesCount");
    if (count) count.textContent = String(companies.length);
  } catch (_) {
    // O dashboard continua utilizável mesmo se a consulta inicial falhar.
  }
}

async function bootstrapAuth() {
  const token = localStorage.getItem(AUTH_TOKEN_KEY);
  if (!token) {
    showLoginScreen();
    return;
  }

  try {
    const response = await fetch(`${API}/auth/me`);
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Sessão inválida.");
    updateUserUI(data);
    await bootstrapAccessibleContext();
    hideLoginScreen();
  } catch (error) {
    localStorage.removeItem(AUTH_TOKEN_KEY);
    showLoginScreen(error.message);
  }
}

function restartViewAnimations(view) {
  if (!view) return;
  view.classList.remove("animate-enter");
  void view.offsetWidth;
  view.classList.add("animate-enter");
}


const appContext = {
  companyId: 1,
  companyName: "Cliente Demonstrativo Alpha",
  competence: null
};

function updateAppContext({
  companyId = appContext.companyId,
  companyName = appContext.companyName,
  competence = appContext.competence
} = {}) {
  appContext.companyId = Number(companyId) || 1;
  appContext.companyName = companyName || `Cliente ${appContext.companyId}`;
  appContext.competence = competence || null;

  const badge =
    document.getElementById("appContextBadge");

  if (badge) {
    const competenceText =
      appContext.competence
        ? ` · ${formatCompetence(appContext.competence)}`
        : "";

    badge.textContent =
      `Contexto: ${appContext.companyName}${competenceText}`;
  }
}

let currentXmlData = null;

let reviewContext = {
  mappingId: null,
  action: null
};

let fiscalDashboardInitialized = false;
let fiscalDashboardData = null;

let gazarraAiInitialized = false;
let gazarraAiStatus = null;
let gazarraAiAgents = [];
let gazarraAiBusy = false;

updateAppContext();


/* =========================================================
   AUTENTICAÇÃO
========================================================= */

const loginForm = document.getElementById("loginForm");
if (loginForm) {
  loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const email = document.getElementById("loginEmail").value.trim();
    const password = document.getElementById("loginPassword").value;
    const message = document.getElementById("loginMessage");
    message?.classList.add("hidden");

    try {
      const response = await fetch(`${API}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json; charset=utf-8" },
        body: JSON.stringify({ email, password })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Não foi possível entrar.");
      localStorage.setItem(AUTH_TOKEN_KEY, data.access_token);
      updateUserUI(data.user);
      await bootstrapAccessibleContext();
      fiscalDashboardInitialized = false;
      gazarraAiInitialized = false;
      hideLoginScreen();
    } catch (error) {
      if (message) {
        message.textContent = error.message;
        message.classList.remove("hidden");
      }
    }
  });
}

const btnLogout = document.getElementById("btnLogout");
if (btnLogout) {
  btnLogout.addEventListener("click", async () => {
    try { await fetch(`${API}/auth/logout`, { method: "POST" }); } catch (_) {}
    localStorage.removeItem(AUTH_TOKEN_KEY);
    currentUser = null;
    fiscalDashboardInitialized = false;
    gazarraAiInitialized = false;
    showLoginScreen();
  });
}

/* =========================================================
   NAVEGAÇÃO
========================================================= */

document.querySelectorAll(".nav").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll(".nav").forEach((item) => {
      item.classList.remove("active");
    });

    document.querySelectorAll(".view").forEach((view) => {
      view.classList.remove("active-view");
    });

    button.classList.add("active");

    document.body.classList.toggle(
      "gazarra-ai-mode",
      button.dataset.view === "gazarra-ai"
    );

    const target = document.getElementById(
      button.dataset.view
    );

    if (target) {
      target.classList.add("active-view");
      restartViewAnimations(target);
    }

    if (button.dataset.view === "mapper") {
      loadMappings();
    }

    if (button.dataset.view === "review") {
      loadReviewQueue();
    }

    if (button.dataset.view === "fiscal-dashboard") {
      initializeFiscalDashboard();
    }

    if (button.dataset.view === "gazarra-ai") {
      initializeGazarraAI();
    }

    if (button.dataset.view === "admin") {
      initializeAdmin();
    }
  });
});


/* =========================================================
   XML
========================================================= */

document
  .getElementById("btnXml")
  .addEventListener("click", processXml);


const xmlFileInput = document.getElementById("xmlFile");
if (xmlFileInput) {
  xmlFileInput.addEventListener("change", () => {
    const name = document.getElementById("xmlFileName");
    if (name) {
      name.textContent = xmlFileInput.files?.[0]?.name || "Selecione um arquivo XML de NF-e";
    }
  });
}


async function processXml() {
  const input =
    document.getElementById("xmlFile");

  const output =
    document.getElementById("xmlResult");

  const loading =
    document.getElementById("xmlLoading");

  if (!input.files.length) {
    output.innerHTML = `
      <div class="message warning">
        Selecione um arquivo XML.
      </div>
    `;

    return;
  }

  const form = new FormData();

  form.append(
    "file",
    input.files[0]
  );

  loading.classList.remove("hidden");

  output.innerHTML = "";

  try {
    const response = await fetch(
      `${API}/xml/preview`,
      {
        method: "POST",
        body: form
      }
    );

    const data = await response.json();

    if (!response.ok) {
      throw new Error(
        data.detail ||
        "Erro ao processar XML."
      );
    }

    currentXmlData = data;

    renderXmlResult(data);

  } catch (error) {
    output.innerHTML = `
      <div class="message error">
        ${escapeHtml(error.message)}
      </div>
    `;

  } finally {
    loading.classList.add("hidden");
  }
}


function renderXmlResult(data) {
  const output =
    document.getElementById("xmlResult");

  if (!data.items || !data.items.length) {
    output.innerHTML = `
      <div class="message warning">
        Nenhum produto foi encontrado no XML.
      </div>
    `;

    return;
  }

  const rows = data.items.map((item) => {
    const quantity = item.quantity
      ? Number(item.quantity).toLocaleString("pt-BR")
      : "-";

    const unitValue = item.unit_value
      ? Number(item.unit_value).toLocaleString(
          "pt-BR",
          {
            style: "currency",
            currency: "BRL"
          }
        )
      : "-";

    return `
      <tr>

        <td>
          ${escapeHtml(
            item.supplier_code || "-"
          )}
        </td>

        <td>
          <strong>
            ${escapeHtml(
              item.description || "-"
            )}
          </strong>
        </td>

        <td>
          ${escapeHtml(
            item.gtin || "-"
          )}
        </td>

        <td>
          ${escapeHtml(
            item.ncm || "-"
          )}
        </td>

        <td>
          ${escapeHtml(
            item.unit || "-"
          )}
        </td>

        <td>
          ${quantity}
        </td>

        <td>
          ${unitValue}
        </td>

      </tr>
    `;
  }).join("");

  output.innerHTML = `

    <div class="document-info">

      <div>
        <span class="small-label">
          Nota fiscal
        </span>

        <strong>
          ${escapeHtml(
            data.invoice_number || "-"
          )}
        </strong>
      </div>


      <div>
        <span class="small-label">
          CNPJ fornecedor
        </span>

        <strong>
          ${escapeHtml(
            data.issuer_cnpj || "-"
          )}
        </strong>
      </div>


      <div>
        <span class="small-label">
          Itens encontrados
        </span>

        <strong>
          ${data.items.length}
        </strong>
      </div>

    </div>


    <div class="table-wrapper">

      <table>

        <thead>
          <tr>
            <th>Código fornecedor</th>
            <th>Produto</th>
            <th>GTIN</th>
            <th>NCM</th>
            <th>Un.</th>
            <th>Qtd.</th>
            <th>Valor unitário</th>
          </tr>
        </thead>

        <tbody>
          ${rows}
        </tbody>

      </table>

    </div>


    <div class="action-row">

      <button id="btnRunMapper">
        Executar Product Mapper
      </button>

    </div>


    <div id="mapperBatchResult"></div>
  `;

  document
    .getElementById("btnRunMapper")
    .addEventListener(
      "click",
      runMapperFromXml
    );
}
/* =========================================================
   PRODUCT MAPPER VIA XML
========================================================= */

async function runMapperFromXml() {
  if (!currentXmlData) {
    return;
  }

  const output =
    document.getElementById(
      "mapperBatchResult"
    );

  output.innerHTML = `
    <div class="loading">
      Executando Product Mapper...
    </div>
  `;

  const payload = {
    supplier_cnpj:
      currentXmlData.issuer_cnpj,

    items:
      currentXmlData.items.map((item) => ({
        supplier_code:
          item.supplier_code,

        description:
          item.description,

        gtin:
          item.gtin,

        ncm:
          item.ncm,

        unit:
          item.unit
      }))
  };

  try {
    const response = await fetch(
      `${API}/matcher/batch?company_id=${appContext.companyId}`,
      {
        method: "POST",

        headers: {
          "Content-Type":
            "application/json"
        },

        body:
          JSON.stringify(payload)
      }
    );

    const data =
      await response.json();

    if (!response.ok) {
      throw new Error(
        data.detail ||
        "Erro ao executar Product Mapper."
      );
    }

    renderMapperResults(data);

  } catch (error) {
    output.innerHTML = `
      <div class="message error">
        ${escapeHtml(error.message)}
      </div>
    `;
  }
}


function renderMapperResults(data) {
  const output =
    document.getElementById(
      "mapperBatchResult"
    );

  if (!data.items || !data.items.length) {
    output.innerHTML = `
      <div class="message warning">
        Nenhum resultado retornado.
      </div>
    `;

    return;
  }

  const rows = data.items.map((item) => {
    const confidence =
      Math.round(
        (item.confidence || 0) * 100
      );

    const status =
      translateStatus(
        item.status
      );

    const reasons =
      (item.reasons || [])
        .map(
          (reason) =>
            escapeHtml(reason)
        )
        .join("<br>");

    let action = "";

    if (item.status === "homologated") {
      action = `
        <div class="action-buttons">

          <button
            class="small-button secondary-button"
            onclick="adjustMapping(
              ${item.mapping_id}
            )"
          >
            Ajustar
          </button>

          <button
            class="small-button danger-button"
            onclick="blockMapping(
              ${item.mapping_id}
            )"
          >
            Bloquear
          </button>

        </div>
      `;
    }

    else if (item.internal_product_id) {
      action = `
        <div class="action-buttons">

          <button
            class="small-button"
            onclick="approveMapping(
              ${item.mapping_id},
              ${item.internal_product_id}
            )"
          >
            Aprovar
          </button>

          <button
            class="small-button secondary-button"
            onclick="adjustMapping(
              ${item.mapping_id}
            )"
          >
            Ajustar
          </button>

          <button
            class="small-button danger-button"
            onclick="blockMapping(
              ${item.mapping_id}
            )"
          >
            Bloquear
          </button>

        </div>
      `;
    }

    else {
      action = `
        <div class="action-buttons">

          <button
            class="small-button secondary-button"
            onclick="adjustMapping(
              ${item.mapping_id}
            )"
          >
            Ajustar
          </button>

          <button
            class="small-button danger-button"
            onclick="blockMapping(
              ${item.mapping_id}
            )"
          >
            Bloquear
          </button>

        </div>
      `;
    }

    return `
      <tr>

        <td>
          <strong>
            ${escapeHtml(
              item.supplier_code || "-"
            )}
          </strong>

          <br>

          <span class="muted">
            ${escapeHtml(
              item.supplier_description || "-"
            )}
          </span>
        </td>


        <td>
          <strong>
            ${escapeHtml(
              item.internal_code || "-"
            )}
          </strong>

          <br>

          <span class="muted">
            ${escapeHtml(
              item.internal_description || "-"
            )}
          </span>
        </td>


        <td>
          <span
            class="confidence ${confidenceClass(
              confidence
            )}"
          >
            ${confidence}%
          </span>
        </td>


        <td>
          ${reasons || "-"}
        </td>


        <td>
          <span
            class="status ${status.className}"
          >
            ${status.label}
          </span>
        </td>


        <td>
          ${action}
        </td>

      </tr>
    `;
  }).join("");

  output.innerHTML = `

    <div class="mapper-heading">

      <div>

        <h3>
          Resultado do Product Mapper
        </h3>

        <p>
          ${data.total_items}
          item(ns) processado(s).
        </p>

      </div>

    </div>


    <div class="table-wrapper">

      <table>

        <thead>

          <tr>
            <th>Produto fornecedor</th>
            <th>Produto interno</th>
            <th>Confiança</th>
            <th>Critérios</th>
            <th>Status</th>
            <th>Ações</th>
          </tr>

        </thead>


        <tbody>
          ${rows}
        </tbody>

      </table>

    </div>
  `;
}


/* =========================================================
   APROVAR MAPPING
========================================================= */

async function approveMapping(
  mappingId,
  productId
) {
  const confirmed = confirm(
    "Confirma a homologação deste De/Para?"
  );

  if (!confirmed) {
    return;
  }

  try {
    const response = await fetch(
      `${API}/mappings/${mappingId}/review`,
      {
        method: "POST",

        headers: {
          "Content-Type":
            "application/json"
        },

        body:
          JSON.stringify({
            action:
              "approve",

            target_product_id:
              productId,

            reviewed_by:
              "Ysa",

            rationale:
              "Homologação realizada pela interface da POC"
          })
      }
    );

    const data =
      await response.json();

    if (!response.ok) {
      throw new Error(
        data.detail ||
        "Erro ao homologar."
      );
    }

    alert(
      "De/Para homologado com sucesso."
    );

    if (currentXmlData) {
      await runMapperFromXml();
    }

    await loadMappings();
    await loadReviewQueue();

  } catch (error) {
    alert(
      error.message
    );
  }
}
/* =========================================================
   PRODUTOS INTERNOS
========================================================= */

async function getInternalProducts() {
  const response = await fetch(
    `${API}/products/${appContext.companyId}`
  );

  const data =
    await response.json();

  if (!response.ok) {
    throw new Error(
      data.detail ||
      "Erro ao carregar produtos internos."
    );
  }

  return data;
}


/* =========================================================
   AJUSTAR MAPPING
========================================================= */

async function adjustMapping(mappingId) {
  try {
    const products =
      await getInternalProducts();

    if (!products.length) {
      alert(
        "Não existem produtos internos cadastrados."
      );

      return;
    }

    reviewContext = {
      mappingId:
        mappingId,

      action:
        "adjust"
    };

    const modal =
      document.getElementById(
        "reviewModal"
      );

    const productGroup =
      document.getElementById(
        "modalProductGroup"
      );

    const select =
      document.getElementById(
        "modalProductSelect"
      );

    const rationale =
      document.getElementById(
        "modalRationale"
      );

    const title =
      document.getElementById(
        "modalTitle"
      );

    const description =
      document.getElementById(
        "modalDescription"
      );

    const confirmButton =
      document.getElementById(
        "btnConfirmModal"
      );

    title.textContent =
      "Ajustar De/Para";

    description.textContent =
      "Selecione o produto interno correto e registre a justificativa.";

    confirmButton.textContent =
      "Confirmar ajuste";

    productGroup.classList.remove(
      "hidden"
    );

    modal.classList.remove(
      "modal-danger-mode"
    );

    select.innerHTML =
      products.map((product) => `
        <option
          value="${product.id}"
        >
          ${escapeHtml(
            product.internal_code
          )}
          —
          ${escapeHtml(
            product.description
          )}
        </option>
      `).join("");

    rationale.value =
      "Correspondência ajustada manualmente durante a homologação.";

    clearModalMessage();

    modal.classList.remove(
      "hidden"
    );

  } catch (error) {
    alert(
      error.message
    );
  }
}


/* =========================================================
   BLOQUEAR MAPPING
========================================================= */

function blockMapping(mappingId) {
  reviewContext = {
    mappingId:
      mappingId,

    action:
      "block"
  };

  const modal =
    document.getElementById(
      "reviewModal"
    );

  const productGroup =
    document.getElementById(
      "modalProductGroup"
    );

  const rationale =
    document.getElementById(
      "modalRationale"
    );

  const title =
    document.getElementById(
      "modalTitle"
    );

  const description =
    document.getElementById(
      "modalDescription"
    );

  const confirmButton =
    document.getElementById(
      "btnConfirmModal"
    );

  title.textContent =
    "Bloquear correspondência";

  description.textContent =
    "O vínculo deixará de ser considerado homologado.";

  confirmButton.textContent =
    "Confirmar bloqueio";

  productGroup.classList.add(
    "hidden"
  );

  modal.classList.add(
    "modal-danger-mode"
  );

  rationale.value =
    "Correspondência não confirmada durante a revisão humana.";

  clearModalMessage();

  modal.classList.remove(
    "hidden"
  );
}


/* =========================================================
   CONTROLE DO MODAL
========================================================= */

function closeReviewModal() {
  const modal =
    document.getElementById(
      "reviewModal"
    );

  modal.classList.add(
    "hidden"
  );

  modal.classList.remove(
    "modal-danger-mode"
  );

  reviewContext = {
    mappingId:
      null,

    action:
      null
  };

  clearModalMessage();
}


function showModalMessage(message) {
  const element =
    document.getElementById(
      "modalMessage"
    );

  element.textContent =
    message;

  element.classList.remove(
    "hidden"
  );
}


function clearModalMessage() {
  const element =
    document.getElementById(
      "modalMessage"
    );

  element.textContent =
    "";

  element.classList.add(
    "hidden"
  );
}


/* =========================================================
   CONFIRMAR MODAL
========================================================= */

async function submitReviewModal() {
  if (
    !reviewContext.mappingId ||
    !reviewContext.action
  ) {
    return;
  }

  const mappingId =
    reviewContext.mappingId;

  const action =
    reviewContext.action;

  const rationale =
    document
      .getElementById(
        "modalRationale"
      )
      .value
      .trim();

  if (!rationale) {
    showModalMessage(
      "Informe uma justificativa para continuar."
    );

    return;
  }

  let productId =
    null;

  if (action === "adjust") {
    productId = Number(
      document
        .getElementById(
          "modalProductSelect"
        )
        .value
    );

    if (!productId) {
      showModalMessage(
        "Selecione um produto interno."
      );

      return;
    }
  }

  const confirmButton =
    document.getElementById(
      "btnConfirmModal"
    );

  const originalText =
    confirmButton.textContent;

  confirmButton.disabled =
    true;

  confirmButton.textContent =
    "Processando...";

  try {
    const response = await fetch(
      `${API}/mappings/${mappingId}/review`,
      {
        method:
          "POST",

        headers: {
          "Content-Type":
            "application/json"
        },

        body:
          JSON.stringify({
            action:
              action,

            target_product_id:
              productId,

            reviewed_by:
              "Ysa",

            rationale:
              rationale
          })
      }
    );

    const data =
      await response.json();

    if (!response.ok) {
      throw new Error(
        data.detail ||
        "Não foi possível registrar a revisão."
      );
    }

    closeReviewModal();

    if (action === "block") {
      alert(
        "Correspondência bloqueada."
      );
    }

    if (action === "adjust") {
      alert(
        "De/Para ajustado e homologado."
      );
    }

    if (currentXmlData) {
      await runMapperFromXml();
    }

    await loadMappings();
    await loadReviewQueue();

  } catch (error) {
    showModalMessage(
      error.message
    );

  } finally {
    confirmButton.disabled =
      false;

    confirmButton.textContent =
      originalText;
  }
}


/* =========================================================
   EVENTOS DO MODAL
========================================================= */

document
  .getElementById(
    "btnCloseModal"
  )
  .addEventListener(
    "click",
    closeReviewModal
  );


document
  .getElementById(
    "btnCancelModal"
  )
  .addEventListener(
    "click",
    closeReviewModal
  );


document
  .getElementById(
    "btnConfirmModal"
  )
  .addEventListener(
    "click",
    submitReviewModal
  );


document
  .getElementById(
    "reviewModal"
  )
  .addEventListener(
    "click",
    (event) => {
      if (
        event.target.id ===
        "reviewModal"
      ) {
        closeReviewModal();
      }
    }
  );


document.addEventListener(
  "keydown",
  (event) => {
    if (event.key === "Escape") {
      const modal =
        document.getElementById(
          "reviewModal"
        );

      if (
        !modal.classList.contains(
          "hidden"
        )
      ) {
        closeReviewModal();
      }
    }
  }
);
/* =========================================================
   MAPPER INDIVIDUAL
========================================================= */

document
  .getElementById(
    "btnMatch"
  )
  .addEventListener(
    "click",
    testIndividualMatch
  );


async function testIndividualMatch() {
  const description =
    document.getElementById(
      "supplierDescription"
    ).value;

  const gtin =
    document.getElementById(
      "supplierGtin"
    ).value;

  const output =
    document.getElementById(
      "matchResult"
    );

  output.innerHTML = `
    <div class="loading">
      Calculando correspondência...
    </div>
  `;

  const payload = {
    supplier_product: {
      supplier_code:
        "SUP-TEST",

      description:
        description,

      gtin:
        gtin,

      ncm:
        "17019900",

      unit:
        "UN"
    },

    candidates: [
      {
        internal_code:
          "PRD-001",

        description:
          "Açúcar Cristal 5 KG",

        gtin:
          "7890000000011",

        ncm:
          "17019900",

        unit:
          "UN"
      },

      {
        internal_code:
          "PRD-002",

        description:
          "Açúcar Refinado 1 KG",

        gtin:
          "7899999999999",

        ncm:
          "17019900",

        unit:
          "UN"
      }
    ]
  };

  try {
    const response = await fetch(
      `${API}/matcher/suggest`,
      {
        method:
          "POST",

        headers: {
          "Content-Type":
            "application/json"
        },

        body:
          JSON.stringify(
            payload
          )
      }
    );

    const data =
      await response.json();

    if (!response.ok) {
      throw new Error(
        data.detail ||
        "Erro ao gerar sugestão."
      );
    }

    const confidence =
      Math.round(
        (data.confidence || 0) * 100
      );

    output.innerHTML = `

      <div class="suggestion-card">

        <span class="small-label">
          Produto sugerido
        </span>

        <h3>
          ${escapeHtml(
            data.internal_code || "-"
          )}
        </h3>

        <p>
          Confiança:
          <strong>
            ${confidence}%
          </strong>
        </p>

        <p>
          Status:
          <strong>
            ${escapeHtml(
              data.status || "-"
            )}
          </strong>
        </p>

        <p>
          Critérios:
        </p>

        <ul>
          ${(data.reasons || [])
            .map(
              (item) =>
                `<li>${escapeHtml(item)}</li>`
            )
            .join("")}
        </ul>

      </div>
    `;

  } catch (error) {
    output.innerHTML = `
      <div class="message error">
        ${escapeHtml(error.message)}
      </div>
    `;
  }
}


function updateMapperVisualKpis(items = []) {
  const homologated = items.filter((item) => item.status === "homologated" && item.approved === true).length;
  const review = items.filter((item) => item.status === "review" || item.status === "auto_candidate").length;
  const blocked = items.filter((item) => item.status === "blocked").length;
  const pending = items.filter((item) => item.status !== "homologated" || item.approved !== true).length;

  const values = {
    mapperPendingKpi: pending,
    mapperHomologatedKpi: homologated,
    mapperReviewKpi: review,
    mapperBlockedKpi: blocked
  };

  Object.entries(values).forEach(([id, value]) => {
    const el = document.getElementById(id);
    if (el) el.textContent = String(value);
  });
}

/* =========================================================
   HISTÓRICO DE MAPPINGS
========================================================= */

document
  .getElementById(
    "btnLoadMappings"
  )
  .addEventListener(
    "click",
    loadMappings
  );


async function loadMappings() {
  const output =
    document.getElementById(
      "mappingsResult"
    );

  output.innerHTML = `
    <div class="loading">
      Carregando homologações...
    </div>
  `;

  try {
    const response = await fetch(
      `${API}/mappings?company_id=${appContext.companyId}`
    );

    const data =
      await response.json();

    if (!response.ok) {
      throw new Error(
        data.detail ||
        "Erro ao carregar homologações."
      );
    }

    updateMapperVisualKpis(data || []);

    if (!data.length) {
      output.innerHTML = `
        <div class="message">
          Nenhum De/Para registrado.
        </div>
      `;

      return;
    }

    const rows =
      data.map((item) => {
        const confidence =
          Math.round(
            (item.confidence || 0) * 100
          );

        const status =
          translateStatus(
            item.status
          );

        return `
          <tr>

            <td>
              ${escapeHtml(
                item.supplier_code || "-"
              )}
            </td>

            <td>
              ${escapeHtml(
                item.supplier_description || "-"
              )}
            </td>

            <td>
              ${escapeHtml(
                item.internal_code || "-"
              )}
            </td>

            <td>
              ${escapeHtml(
                item.internal_description || "-"
              )}
            </td>

            <td>
              ${confidence}%
            </td>

            <td>
              <span
                class="status ${status.className}"
              >
                ${status.label}
              </span>
            </td>

            <td>
              ${escapeHtml(
                item.reviewed_by || "-"
              )}
            </td>

            <td>

              <div class="action-buttons">

                <button
                  class="small-button secondary-button"
                  onclick="adjustMapping(
                    ${item.id}
                  )"
                >
                  Ajustar
                </button>

                <button
                  class="small-button danger-button"
                  onclick="blockMapping(
                    ${item.id}
                  )"
                >
                  Bloquear
                </button>

              </div>

            </td>

          </tr>
        `;
      }).join("");

    output.innerHTML = `

      <div class="table-wrapper">

        <table>

          <thead>

            <tr>
              <th>Código fornecedor</th>
              <th>Produto fornecedor</th>
              <th>Código interno</th>
              <th>Produto interno</th>
              <th>Confiança</th>
              <th>Status</th>
              <th>Revisado por</th>
              <th>Ações</th>
            </tr>

          </thead>


          <tbody>
            ${rows}
          </tbody>

        </table>

      </div>
    `;

  } catch (error) {
    output.innerHTML = `
      <div class="message error">
        ${escapeHtml(error.message)}
      </div>
    `;
  }
}
/* =========================================================
   FILA DE REVISÃO HUMANA
========================================================= */

const btnRefreshReview =
  document.getElementById("btnRefreshReview");


if (btnRefreshReview) {
  btnRefreshReview.addEventListener(
    "click",
    loadReviewQueue
  );
}


async function loadReviewQueue() {
  const output =
    document.getElementById("reviewQueue");

  const totalElement =
    document.getElementById("reviewTotal");

  const pendingElement =
    document.getElementById("reviewPending");

  const blockedElement =
    document.getElementById("reviewBlocked");

  if (!output) {
    return;
  }

  output.innerHTML = `
    <div class="loading">
      Carregando fila de revisão...
    </div>
  `;

  try {
    const response = await fetch(
      `${API}/mappings?company_id=${appContext.companyId}`
    );

    const data =
      await response.json();

    if (!response.ok) {
      throw new Error(
        data.detail ||
        "Erro ao carregar a fila de revisão."
      );
    }

    const queue =
      (data || []).filter((item) =>
        item.status !== "homologated" ||
        item.approved !== true
      );

    const pending =
      queue.filter((item) =>
        item.status === "review" ||
        item.status === "auto_candidate"
      );

    const blocked =
      queue.filter((item) =>
        item.status === "blocked"
      );

    totalElement.textContent =
      String(queue.length);

    pendingElement.textContent =
      String(pending.length);

    blockedElement.textContent =
      String(blocked.length);

    if (!queue.length) {
      output.innerHTML = `
        <div class="review-empty">
          Nenhum item aguardando revisão para
          ${escapeHtml(appContext.companyName)}.
        </div>
      `;

      return;
    }

    const rows =
      queue.map((item) => {
        const confidence =
          Math.round(
            Number(item.confidence || 0) * 100
          );

        const status =
          translateStatus(item.status);

        const internalId =
          item.internal_product_id ||
          item.target_product_id ||
          null;

        let actions = `
          <button
            class="small-button secondary-button"
            onclick="adjustMapping(${item.id})"
          >
            Ajustar
          </button>
        `;

        if (
          item.status !== "blocked" &&
          internalId
        ) {
          actions = `
            <button
              class="small-button"
              onclick="approveMapping(${item.id}, ${internalId})"
            >
              Aprovar
            </button>
            ${actions}
          `;
        }

        if (item.status !== "blocked") {
          actions += `
            <button
              class="small-button danger-button"
              onclick="blockMapping(${item.id})"
            >
              Bloquear
            </button>
          `;
        }

        return `
          <tr>
            <td>
              <div class="review-product">
                <span class="review-product-code">
                  ${escapeHtml(item.supplier_code || "-")}
                </span>
                <span class="review-product-description">
                  ${escapeHtml(item.supplier_description || "-")}
                </span>
              </div>
            </td>

            <td>
              <div class="review-product">
                <span class="review-product-code">
                  ${escapeHtml(item.internal_code || "-")}
                </span>
                <span class="review-product-description">
                  ${escapeHtml(item.internal_description || "Sem produto interno definido")}
                </span>
              </div>
            </td>

            <td>
              <span class="confidence ${confidenceClass(confidence)}">
                ${confidence}%
              </span>
            </td>

            <td>
              <span class="status ${status.className}">
                ${status.label}
              </span>
            </td>

            <td>
              <div class="action-buttons">
                ${actions}
              </div>
            </td>
          </tr>
        `;
      }).join("");

    output.innerHTML = `
      <div class="review-context-note">
        Empresa em contexto:
        <strong>${escapeHtml(appContext.companyName)}</strong>
      </div>

      <div class="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>Produto fornecedor</th>
              <th>Produto interno</th>
              <th>Confiança</th>
              <th>Status</th>
              <th>Ações</th>
            </tr>
          </thead>
          <tbody>
            ${rows}
          </tbody>
        </table>
      </div>
    `;

  } catch (error) {
    totalElement.textContent = "0";
    pendingElement.textContent = "0";
    blockedElement.textContent = "0";

    output.innerHTML = `
      <div class="message error">
        ${escapeHtml(error.message)}
      </div>
    `;
  }
}


/* =========================================================
   DASHBOARD FISCAL
========================================================= */

const fiscalCompanySelect =
  document.getElementById("fiscalCompany");

const fiscalCompanySearch =
  document.getElementById("fiscalCompanySearch");

const fiscalCnpjSearch =
  document.getElementById("fiscalCnpjSearch");

const fiscalCompanySuggestions =
  document.getElementById("fiscalCompanySuggestions");

const fiscalCompetenceSelect =
  document.getElementById("fiscalCompetence");

const btnFiscalRefresh =
  document.getElementById("btnFiscalRefresh");


if (fiscalCompanySelect) {
  fiscalCompanySelect.addEventListener("change", async () => {
    const companyId = Number(fiscalCompanySelect.value);
    const selected = fiscalCompaniesCache.find(
      (company) => Number(company.id) === companyId
    );

    if (selected) {
      syncCompanySearchFields(selected);
      updateAppContext({
        companyId: selected.id,
        companyName: selected.name,
        competence: null
      });
      await loadFiscalCompetences(companyId, true);
    }
  });
}

function normalizeCnpjSearch(value) {
  return String(value || "").replace(/\D/g, "");
}

function syncCompanySearchFields(company) {
  if (fiscalCompanySearch) fiscalCompanySearch.value = company?.name || "";
  if (fiscalCnpjSearch) fiscalCnpjSearch.value = company?.cnpj || "";
}

function hideCompanySuggestions() {
  fiscalCompanySuggestions?.classList.add("hidden");
}

function renderCompanySuggestions(companies) {
  if (!fiscalCompanySuggestions) return;
  if (!companies.length) {
    fiscalCompanySuggestions.innerHTML = '<div class="company-no-result">Nenhuma empresa encontrada para este perfil.</div>';
    fiscalCompanySuggestions.classList.remove("hidden");
    return;
  }

  fiscalCompanySuggestions.innerHTML = companies.map((company) => `
    <button type="button" class="company-suggestion" data-company-id="${company.id}">
      <span><strong>${escapeHtml(company.name)}</strong><small>${escapeHtml(company.cnpj || "CNPJ não informado")}</small></span>
      <b>Selecionar</b>
    </button>
  `).join("");
  fiscalCompanySuggestions.classList.remove("hidden");

  fiscalCompanySuggestions.querySelectorAll(".company-suggestion").forEach((button) => {
    button.addEventListener("click", () => {
      selectFiscalCompany(Number(button.dataset.companyId));
    });
  });
}

async function searchFiscalCompanies(query = "") {
  try {
    const params = new URLSearchParams();
    if (query.trim()) params.set("search", query.trim());
    const response = await fetch(`${API}/fiscal/companies?${params.toString()}`);
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Erro ao pesquisar empresas.");
    fiscalCompaniesCache = data;
    renderCompanySuggestions(data);
    return data;
  } catch (error) {
    showFiscalMessage(error.message, "error");
    return [];
  }
}

async function selectFiscalCompany(companyId) {
  let selected = fiscalCompaniesCache.find((company) => Number(company.id) === Number(companyId));
  if (!selected) {
    const all = await searchFiscalCompanies("");
    selected = all.find((company) => Number(company.id) === Number(companyId));
  }
  if (!selected) return;

  fiscalCompanySelect.innerHTML = `
    <option value="${selected.id}">${escapeHtml(selected.name)}</option>
  `;
  fiscalCompanySelect.value = String(selected.id);
  syncCompanySearchFields(selected);
  hideCompanySuggestions();
  updateAppContext({
    companyId: selected.id,
    companyName: selected.name,
    competence: null
  });
  await loadFiscalCompetences(selected.id, true);
}

function scheduleCompanySearch(value) {
  clearTimeout(companySearchTimer);
  companySearchTimer = setTimeout(() => searchFiscalCompanies(value), 220);
}

if (fiscalCompanySearch) {
  fiscalCompanySearch.addEventListener("focus", () => searchFiscalCompanies(fiscalCompanySearch.value));
  fiscalCompanySearch.addEventListener("input", () => scheduleCompanySearch(fiscalCompanySearch.value));
}

if (fiscalCnpjSearch) {
  fiscalCnpjSearch.addEventListener("focus", () => searchFiscalCompanies(fiscalCnpjSearch.value));
  fiscalCnpjSearch.addEventListener("input", () => scheduleCompanySearch(normalizeCnpjSearch(fiscalCnpjSearch.value)));
}

document.addEventListener("click", (event) => {
  if (!event.target.closest(".company-search-group") && event.target !== fiscalCnpjSearch) {
    hideCompanySuggestions();
  }
});

if (fiscalCompetenceSelect) {
  fiscalCompetenceSelect.addEventListener("change", async () => {
    if (fiscalCompanySelect.value && fiscalCompetenceSelect.value) {
      updateAppContext({ competence: fiscalCompetenceSelect.value });
      await loadFiscalDashboard();
    }
  });
}

if (btnFiscalRefresh) {
  btnFiscalRefresh.addEventListener("click", loadFiscalDashboard);
}

async function initializeFiscalDashboard() {
  if (fiscalDashboardInitialized) return;
  fiscalDashboardInitialized = true;
  await loadFiscalCompanies();
}

async function loadFiscalCompanies() {
  showFiscalLoading(true);
  clearFiscalMessage();

  try {
    const response = await fetch(`${API}/fiscal/companies`);
    const companies = await response.json();
    if (!response.ok) throw new Error(companies.detail || "Erro ao carregar clientes fiscais.");
    if (!companies.length) throw new Error("Nenhuma empresa foi atribuída a este usuário.");

    fiscalCompaniesCache = companies;
    const preferredCompany = companies.find(
      (company) => Number(company.id) === Number(appContext.companyId)
    ) || companies[0];

    fiscalCompanySelect.innerHTML = companies.map((company) => `
      <option value="${company.id}">${escapeHtml(company.name)}</option>
    `).join("");
    fiscalCompanySelect.value = String(preferredCompany.id);
    syncCompanySearchFields(preferredCompany);
    updateAppContext({
      companyId: preferredCompany.id,
      companyName: preferredCompany.name
    });

    await loadFiscalCompetences(preferredCompany.id, true);
  } catch (error) {
    showFiscalMessage(error.message, "error");
  } finally {
    showFiscalLoading(false);
  }
}


async function loadFiscalCompetences(
  companyId,
  loadDashboardAfter = false
) {
  if (!companyId) {
    fiscalCompetenceSelect.innerHTML = `
      <option value="">
        Selecione um cliente
      </option>
    `;

    return;
  }

  fiscalCompetenceSelect.disabled = true;

  try {
    const response = await fetch(
      `${API}/fiscal/companies/${companyId}/competences`
    );

    const competences =
      await response.json();

    if (!response.ok) {
      throw new Error(
        competences.detail ||
        "Erro ao carregar competências."
      );
    }

    const ordered = [
      ...competences
    ].reverse();

    fiscalCompetenceSelect.innerHTML =
      ordered.map((competence) => `
        <option value="${escapeHtml(competence)}">
          ${formatCompetence(competence)}
        </option>
      `).join("");

    if (ordered.length) {
      const preferredCompetence =
        ordered.includes(appContext.competence)
          ? appContext.competence
          : ordered[0];

      fiscalCompetenceSelect.value =
        preferredCompetence;

      updateAppContext({
        competence: preferredCompetence
      });
    }

    if (
      loadDashboardAfter &&
      ordered.length
    ) {
      await loadFiscalDashboard();
    }

  } catch (error) {
    showFiscalMessage(
      error.message,
      "error"
    );

  } finally {
    fiscalCompetenceSelect.disabled = false;
  }
}


async function loadFiscalDashboard() {
  const companyId =
    Number(fiscalCompanySelect.value);

  const competence =
    fiscalCompetenceSelect.value;

  if (!companyId || !competence) {
    showFiscalMessage(
      "Selecione cliente e competência.",
      "warning"
    );

    return;
  }

  showFiscalLoading(true);
  clearFiscalMessage();

  try {
    const params =
      new URLSearchParams({
        company_id:
          String(companyId),
        competence:
          competence
      });

    const response = await fetch(
      `${API}/fiscal/dashboard?${params.toString()}`
    );

    const data =
      await response.json();

    if (!response.ok) {
      throw new Error(
        data.detail ||
        "Erro ao carregar Dashboard Fiscal."
      );
    }

    fiscalDashboardData = data;

    updateAppContext({
      companyId: data.company.id,
      companyName: data.company.name,
      competence: data.competence
    });

    renderFiscalDashboard(data);

  } catch (error) {
    document
      .getElementById("fiscalContent")
      .classList.add("hidden");

    showFiscalMessage(
      error.message,
      "error"
    );

  } finally {
    showFiscalLoading(false);
  }
}


function renderFiscalDashboard(data) {
  const content =
    document.getElementById("fiscalContent");

  content.classList.remove("hidden");

  renderFiscalMetadata(
    data.metadata
  );

  document.getElementById(
    "fiscalCompanyName"
  ).textContent =
    data.company.name || "—";

  document.getElementById(
    "fiscalCompanyCnpj"
  ).textContent =
    data.company.cnpj || "—";

  document.getElementById(
    "fiscalCompanyRegime"
  ).textContent =
    data.company.tax_regime || "—";

  document.getElementById(
    "fiscalCompanyLocation"
  ).textContent =
    `${data.company.city || "—"} / ${data.company.state || "—"}`;


  document.getElementById(
    "kpiRevenueWithoutSt"
  ).textContent =
    formatCurrency(
      data.revenue.without_st
    );

  document.getElementById(
    "kpiRevenueWithSt"
  ).textContent =
    formatCurrency(
      data.revenue.with_st
    );

  document.getElementById(
    "kpiDas"
  ).textContent =
    formatCurrency(
      data.taxes.das
    );

  document.getElementById(
    "kpiEffectiveRate"
  ).textContent =
    formatPercent(
      data.taxes.effective_rate
    );

  document.getElementById(
    "kpiSt"
  ).textContent =
    formatCurrency(
      data.taxes.st
    );

  document.getElementById(
    "kpiDifal"
  ).textContent =
    formatCurrency(
      data.taxes.difal
    );


  renderFiscalComparison(
    "fiscalMonthlyComparison",
    data.monthly_comparison
  );

  renderFiscalComparison(
    "fiscalYearlyComparison",
    data.yearly_comparison
  );

  renderFiscalHistory(
    data.history || []
  );

  renderSimples(
    data.simples
  );

  renderStTable(
    data.st_by_state || []
  );

  renderDifalTable(
    data.difal_details || []
  );

  renderCertificates(
    data.certificates || []
  );

  renderObligations(
    data.obligations || []
  );
}


function renderFiscalMetadata(metadata) {
  const note =
    document.getElementById("fiscalSourceNote");

  if (!note) {
    return;
  }

  if (!metadata) {
    note.textContent =
      "Fonte atual: ambiente demonstrativo.";

    return;
  }

  const sourceLabels = {
    mock: "MockFiscalProvider",
    dominio: "Domínio"
  };

  const source =
    sourceLabels[metadata.source] ||
    metadata.source ||
    "Não informada";

  const environment =
    metadata.environment === "demo"
      ? "ambiente demonstrativo"
      : metadata.environment || "ambiente não informado";

  const generatedAt =
    metadata.generated_at
      ? ` · atualizado em ${formatDateTime(metadata.generated_at)}`
      : "";

  note.textContent =
    `Fonte: ${source} · ${environment}${generatedAt}`;
}


function renderFiscalComparison(
  elementId,
  items
) {
  const element =
    document.getElementById(elementId);

  if (!items || !items.length) {
    element.innerHTML = `
      <div class="fiscal-empty">
        Comparativo indisponível para esta competência.
      </div>
    `;

    return;
  }

  element.innerHTML =
    items.map((item) => {
      const variation =
        Number(item.variation_percentage || 0);

      const directionClass =
        variation > 0
          ? "trend-up"
          : variation < 0
            ? "trend-down"
            : "trend-neutral";

      const arrow =
        variation > 0
          ? "↑"
          : variation < 0
            ? "↓"
            : "→";

      return `
        <div class="fiscal-comparison-item">

          <div>
            <span>${escapeHtml(item.name)}</span>
            <strong>
              ${formatCurrency(item.current_value)}
            </strong>
          </div>

          <div class="fiscal-comparison-meta">
            <small>
              Anterior:
              ${formatCurrency(item.previous_value)}
            </small>

            <b class="${directionClass}">
              ${arrow}
              ${formatPercent(Math.abs(variation))}
            </b>
          </div>

        </div>
      `;
    }).join("");
}


function renderFiscalHistory(history) {
  if (!history.length) {
    return;
  }

  const last =
    history[history.length - 1];

  document.getElementById(
    "historyRevenueValue"
  ).textContent =
    formatCurrency(
      last.revenue_without_st
    );

  document.getElementById(
    "historyDasValue"
  ).textContent =
    formatCurrency(
      last.das
    );

  document.getElementById(
    "historyStValue"
  ).textContent =
    formatCurrency(
      last.st
    );

  document.getElementById(
    "chartRevenue"
  ).innerHTML =
    buildSparkline(
      history,
      "revenue_without_st"
    );

  document.getElementById(
    "chartDas"
  ).innerHTML =
    buildSparkline(
      history,
      "das"
    );

  document.getElementById(
    "chartSt"
  ).innerHTML =
    buildSparkline(
      history,
      "st"
    );
}


function buildSparkline(
  history,
  key
) {
  const values =
    history.map(
      (item) => Number(item[key] || 0)
    );

  const width = 320;
  const height = 125;
  const padding = 14;

  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;

  const points =
    values.map((value, index) => {
      const x =
        padding +
        (
          index /
          Math.max(values.length - 1, 1)
        ) *
        (width - padding * 2);

      const y =
        height -
        padding -
        (
          (value - min) /
          range
        ) *
        (height - padding * 2);

      return {
        x,
        y,
        value,
        competence:
          history[index].competence
      };
    });

  const polyline =
    points
      .map(
        (point) =>
          `${point.x.toFixed(1)},${point.y.toFixed(1)}`
      )
      .join(" ");

  const circles =
    points.map((point) => `
      <circle
        cx="${point.x.toFixed(1)}"
        cy="${point.y.toFixed(1)}"
        r="3"
      >
        <title>
          ${formatCompetence(point.competence)} — ${formatCurrency(point.value)}
        </title>
      </circle>
    `).join("");

  const firstCompetence =
    history[0].competence;

  const lastCompetence =
    history[history.length - 1].competence;

  return `
    <svg
      class="fiscal-sparkline"
      viewBox="0 0 ${width} ${height}"
      role="img"
      aria-label="Histórico de ${escapeHtml(key)}"
    >
      <line
        x1="${padding}"
        y1="${height - padding}"
        x2="${width - padding}"
        y2="${height - padding}"
        class="sparkline-axis"
      ></line>

      <polyline
        points="${polyline}"
        pathLength="1"
        class="sparkline-line"
      ></polyline>

      ${circles}
    </svg>

    <div class="fiscal-chart-period">
      <span>${formatCompetence(firstCompetence)}</span>
      <span>${formatCompetence(lastCompetence)}</span>
    </div>
  `;
}


function renderSimples(simples) {
  if (!simples) {
    return;
  }

  document.getElementById(
    "simplesAccumulated"
  ).textContent =
    formatCurrency(
      simples.accumulated
    );

  document.getElementById(
    "simplesUsedPercentage"
  ).textContent =
    formatPercent(
      simples.used_percentage
    );

  document.getElementById(
    "simplesProgressBar"
  ).style.width =
    `${clampPercentage(simples.used_percentage)}%`;

  document.getElementById(
    "simplesLimitText"
  ).textContent =
    `${formatCurrency(simples.accumulated)} utilizados de ${formatCurrency(simples.limit)} — ${formatPercent(simples.remaining_percentage)} disponíveis.`;

  document.getElementById(
    "simplesSublimit"
  ).textContent =
    formatCurrency(
      simples.icms_iss_sublimit
    );

  document.getElementById(
    "simplesSublimitUsed"
  ).textContent =
    formatPercent(
      simples.icms_iss_used_percentage
    );

  document.getElementById(
    "simplesSublimitProgressBar"
  ).style.width =
    `${clampPercentage(simples.icms_iss_used_percentage)}%`;

  document.getElementById(
    "simplesSublimitText"
  ).textContent =
    `${formatPercent(simples.icms_iss_used_percentage)} do sublimite utilizado — ${formatPercent(simples.icms_iss_remaining_percentage)} disponíveis.`;
}


function renderStTable(items) {
  const output =
    document.getElementById("fiscalStTable");

  if (!items.length) {
    output.innerHTML = `
      <div class="fiscal-empty">
        Sem operações de ST para exibir.
      </div>
    `;

    return;
  }

  const rows =
    items.map((item) => `
      <tr>
        <td>${escapeHtml(item.state)}</td>
        <td>${escapeHtml(item.cfop)}</td>
        <td>${escapeHtml(item.product)}</td>
        <td>${formatCurrency(item.invoice_value)}</td>
        <td><strong>${formatCurrency(item.st_value)}</strong></td>
      </tr>
    `).join("");

  output.innerHTML = `
    <div class="table-wrapper fiscal-table-compact">
      <table>
        <thead>
          <tr>
            <th>UF</th>
            <th>CFOP</th>
            <th>Produto</th>
            <th>Operação</th>
            <th>ST</th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
  `;
}


function renderDifalTable(items) {
  const output =
    document.getElementById("fiscalDifalTable");

  if (!items.length) {
    output.innerHTML = `
      <div class="fiscal-empty">
        Sem lançamentos de DIFAL para exibir.
      </div>
    `;

    return;
  }

  const rows =
    items.map((item) => `
      <tr>
        <td>${escapeHtml(item.supplier)}</td>
        <td>${escapeHtml(item.invoice_number)}</td>
        <td>${formatCurrency(item.document_value)}</td>
        <td>${formatCurrency(item.calculation_base)}</td>
        <td><strong>${formatCurrency(item.icms_advance)}</strong></td>
      </tr>
    `).join("");

  output.innerHTML = `
    <div class="table-wrapper fiscal-table-compact">
      <table>
        <thead>
          <tr>
            <th>Fornecedor</th>
            <th>NF</th>
            <th>Documento</th>
            <th>Base</th>
            <th>ICMS</th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
  `;
}


function renderCertificates(items) {
  const output =
    document.getElementById("fiscalCertificates");

  if (!items.length) {
    output.innerHTML = `
      <div class="fiscal-empty">
        Nenhuma certidão cadastrada.
      </div>
    `;

    return;
  }

  output.innerHTML =
    items.map((item) => {
      const statusClass =
        certificateStatusClass(
          item.status
        );

      return `
        <div class="fiscal-certificate-item">

          <div>
            <strong>${escapeHtml(item.type)}</strong>
            <small>
              Validade: ${formatDate(item.expires_at)}
            </small>
          </div>

          <span class="status ${statusClass}">
            ${escapeHtml(item.status)}
          </span>

        </div>
      `;
    }).join("");
}


function renderObligations(items) {
  const output =
    document.getElementById("fiscalObligations");

  if (!items.length) {
    output.innerHTML = `
      <div class="fiscal-empty">
        Nenhuma obrigação para esta competência.
      </div>
    `;

    return;
  }

  const rows =
    items.map((item) => {
      const statusClass =
        item.status === "Entregue"
          ? "status-success"
          : "status-warning";

      return `
        <tr>
          <td><strong>${escapeHtml(item.name)}</strong></td>
          <td>${formatCompetence(item.competence)}</td>
          <td>${formatDate(item.due_at)}</td>
          <td>
            <span class="status ${statusClass}">
              ${escapeHtml(item.status)}
            </span>
          </td>
        </tr>
      `;
    }).join("");

  output.innerHTML = `
    <div class="table-wrapper fiscal-table-compact">
      <table>
        <thead>
          <tr>
            <th>Obrigação</th>
            <th>Competência</th>
            <th>Vencimento</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
  `;
}


function showFiscalLoading(show) {
  const element =
    document.getElementById("fiscalLoading");

  if (!element) {
    return;
  }

  element.classList.toggle(
    "hidden",
    !show
  );
}


function showFiscalMessage(
  message,
  type = ""
) {
  const output =
    document.getElementById("fiscalMessage");

  output.innerHTML = `
    <div class="message ${type}">
      ${escapeHtml(message)}
    </div>
  `;
}


function clearFiscalMessage() {
  const output =
    document.getElementById("fiscalMessage");

  if (output) {
    output.innerHTML = "";
  }
}


function formatCurrency(value) {
  return Number(value || 0).toLocaleString(
    "pt-BR",
    {
      style:
        "currency",
      currency:
        "BRL"
    }
  );
}


function formatPercent(value) {
  return `${Number(value || 0).toLocaleString(
    "pt-BR",
    {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }
  )}%`;
}


function formatCompetence(value) {
  if (!value) {
    return "—";
  }

  const parts =
    String(value).split("-");

  if (parts.length !== 2) {
    return value;
  }

  const months = [
    "Jan",
    "Fev",
    "Mar",
    "Abr",
    "Mai",
    "Jun",
    "Jul",
    "Ago",
    "Set",
    "Out",
    "Nov",
    "Dez"
  ];

  const monthIndex =
    Number(parts[1]) - 1;

  return `${months[monthIndex] || parts[1]}/${parts[0]}`;
}


function formatDate(value) {
  if (!value) {
    return "—";
  }

  const parts =
    String(value).split("-");

  if (parts.length !== 3) {
    return value;
  }

  return `${parts[2]}/${parts[1]}/${parts[0]}`;
}


function formatDateTime(value) {
  if (!value) {
    return "—";
  }

  const date =
    new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString(
    "pt-BR",
    {
      dateStyle: "short",
      timeStyle: "short"
    }
  );
}


function clampPercentage(value) {
  return Math.max(
    0,
    Math.min(
      100,
      Number(value || 0)
    )
  );
}


function certificateStatusClass(status) {
  const normalized =
    String(status || "")
      .toLowerCase();

  if (normalized.includes("regular")) {
    return "status-success";
  }

  if (
    normalized.includes("vencer") ||
    normalized.includes("pendente")
  ) {
    return "status-warning";
  }

  return "status-danger";
}


/* =========================================================
   ISS
========================================================= */

document
  .getElementById(
    "btnIss"
  )
  .addEventListener(
    "click",
    searchIss
  );


async function searchIss() {
  const municipio =
    document.getElementById(
      "issMunicipio"
    ).value;

  const uf =
    document.getElementById(
      "issUf"
    ).value;

  const codigo =
    document.getElementById(
      "issCodigo"
    ).value;

  const output =
    document.getElementById(
      "issResult"
    );

  const params =
    new URLSearchParams();

  if (municipio) {
    params.set(
      "municipio",
      municipio
    );
  }

  if (uf) {
    params.set(
      "uf",
      uf
    );
  }

  if (codigo) {
    params.set(
      "codigo",
      codigo
    );
  }

  output.innerHTML = `
    <div class="loading">
      Consultando...
    </div>
  `;

  try {
    const response = await fetch(
      `${API}/iss/search?${params.toString()}`
    );

    const data =
      await response.json();

    if (!response.ok) {
      throw new Error(
        data.detail ||
        "Erro na consulta."
      );
    }

    if (
      !data.items ||
      !data.items.length
    ) {
      output.innerHTML = `
        <div class="message warning">
          Nenhum resultado encontrado.
        </div>
      `;

      return;
    }

    const rows =
      data.items.map((item) => `
        <tr>

          <td>
            ${escapeHtml(
              item.municipio || "-"
            )}
          </td>

          <td>
            ${escapeHtml(
              item.uf || "-"
            )}
          </td>

          <td>
            ${escapeHtml(
              item.codigo_servico || "-"
            )}
          </td>

          <td>
            ${escapeHtml(
              item.descricao_servico || "-"
            )}
          </td>

          <td>
            ${escapeHtml(
              item.aliquota || "-"
            )}%
          </td>

          <td>
            ${escapeHtml(
              item.vigencia || "-"
            )}
          </td>

        </tr>
      `).join("");

    output.innerHTML = `

      <div class="table-wrapper">

        <table>

          <thead>

            <tr>
              <th>Município</th>
              <th>UF</th>
              <th>Código</th>
              <th>Serviço</th>
              <th>ISS</th>
              <th>Vigência</th>
            </tr>

          </thead>


          <tbody>
            ${rows}
          </tbody>

        </table>

      </div>


      <p class="source-note">
        ${escapeHtml(
          data.source || ""
        )}
      </p>
    `;

  } catch (error) {
    output.innerHTML = `
      <div class="message error">
        ${escapeHtml(error.message)}
      </div>
    `;
  }
}



/* =========================================================
   GAZARRA IA
========================================================= */

const aiCompanySelect =
  document.getElementById("aiCompany");

const aiCompetenceSelect =
  document.getElementById("aiCompetence");

const aiAgentSelect =
  document.getElementById("aiAgent");

const aiInput =
  document.getElementById("aiInput");

const btnAiSend =
  document.getElementById("btnAiSend");

const btnAiClear =
  document.getElementById("btnAiClear");

const fiscalAiInput =
  document.getElementById("fiscalAiInput");

const btnFiscalAiSend =
  document.getElementById("btnFiscalAiSend");


if (aiCompanySelect) {
  aiCompanySelect.addEventListener(
    "change",
    async () => {
      const companyId =
        Number(aiCompanySelect.value);

      const companyName =
        aiCompanySelect.options[
          aiCompanySelect.selectedIndex
        ]?.textContent?.trim();

      updateAppContext({
        companyId,
        companyName,
        competence: null
      });

      await loadAiCompetences(
        companyId,
        true
      );
    }
  );
}


if (aiCompetenceSelect) {
  aiCompetenceSelect.addEventListener(
    "change",
    () => {
      updateAppContext({
        competence:
          aiCompetenceSelect.value
      });

      renderAiContextNote();
    }
  );
}


if (btnAiSend) {
  btnAiSend.addEventListener(
    "click",
    sendAiMessage
  );
}


if (btnAiClear) {
  btnAiClear.addEventListener(
    "click",
    clearAiConversation
  );
}


if (aiInput) {
  aiInput.addEventListener(
    "keydown",
    (event) => {
      if (
        event.key === "Enter" &&
        !event.shiftKey
      ) {
        event.preventDefault();
        sendAiMessage();
      }
    }
  );
}


if (btnFiscalAiSend) {
  btnFiscalAiSend.addEventListener(
    "click",
    () => sendFiscalAiMessage()
  );
}


if (fiscalAiInput) {
  fiscalAiInput.addEventListener(
    "keydown",
    (event) => {
      if (
        event.key === "Enter" &&
        !event.shiftKey
      ) {
        event.preventDefault();
        sendFiscalAiMessage();
      }
    }
  );
}


document
  .querySelectorAll("[data-ai-prompt]")
  .forEach((button) => {
    button.addEventListener(
      "click",
      () => {
        if (!aiInput) {
          return;
        }

        aiInput.value =
          button.dataset.aiPrompt || "";

        sendAiMessage();
      }
    );
  });


document
  .querySelectorAll("[data-ai-mini-prompt]")
  .forEach((button) => {
    button.addEventListener(
      "click",
      () => {
        if (!fiscalAiInput) {
          return;
        }

        fiscalAiInput.value =
          button.dataset.aiMiniPrompt || "";

        sendFiscalAiMessage();
      }
    );
  });


async function initializeGazarraAI() {
  if (gazarraAiInitialized) {
    syncAiControlsWithContext();
    return;
  }

  gazarraAiInitialized = true;

  await Promise.all([
    loadAiStatus(),
    loadAiAgents(),
    loadAiCompanies()
  ]);
}


async function loadAiStatus() {
  try {
    const response = await fetch(
      `${API}/ai/status`
    );

    const data = await response.json();

    if (!response.ok) {
      throw new Error(
        data.detail ||
        "Erro ao consultar status da GAZARRA IA."
      );
    }

    gazarraAiStatus = data;
    renderAiStatus(data);

  } catch (error) {
    renderAiStatus({
      provider: "indisponível",
      agents_loaded: 0,
      data_source: "—",
      environment: "—",
      configured: false
    });
  }
}


function renderAiStatus(data) {
  const providerBadge =
    document.getElementById("aiProviderBadge");

  const agentsBadge =
    document.getElementById("aiAgentsBadge");

  const environmentNote =
    document.getElementById("aiEnvironmentNote");

  const fiscalStatus =
    document.getElementById("fiscalAiStatus");

  if (providerBadge) {
    const provider =
      data.provider || "demo";

    providerBadge.textContent =
      `Provedor: ${provider}`;

    providerBadge.classList.toggle(
      "ai-status-demo",
      provider === "demo"
    );
  }

  if (agentsBadge) {
    agentsBadge.textContent =
      `Agentes: ${data.agents_loaded ?? "—"}`;
  }

  if (environmentNote) {
    environmentNote.textContent =
      `Fonte: ${data.data_source || "—"} · ambiente ${data.environment || "—"}`;
  }

  if (fiscalStatus) {
    fiscalStatus.textContent =
      data.provider === "demo"
        ? "Modo demonstrativo"
        : `IA ativa · ${data.provider}`;

    fiscalStatus.classList.toggle(
      "ai-status-demo",
      data.provider === "demo"
    );
  }
}


async function loadAiAgents() {
  if (!aiAgentSelect) {
    return;
  }

  try {
    const response = await fetch(
      `${API}/ai/agents`
    );

    const agents = await response.json();

    if (!response.ok) {
      throw new Error(
        agents.detail ||
        "Erro ao carregar agentes."
      );
    }

    gazarraAiAgents = agents;

    const grouped = {};

    agents.forEach((agent) => {
      const category =
        agent.category || "Outros";

      if (!grouped[category]) {
        grouped[category] = [];
      }

      grouped[category].push(agent);
    });

    let html = `
      <option value="auto">
        Automático — deixar a IA escolher
      </option>
    `;

    Object
      .keys(grouped)
      .sort()
      .forEach((category) => {
        html += `
          <optgroup label="${escapeHtml(category)}">
            ${grouped[category]
              .map((agent) => `
                <option value="${escapeHtml(agent.name)}">
                  ${escapeHtml(agent.title)}
                </option>
              `)
              .join("")}
          </optgroup>
        `;
      });

    aiAgentSelect.innerHTML = html;

  } catch (error) {
    aiAgentSelect.innerHTML = `
      <option value="auto">
        Automático
      </option>
    `;
  }
}


async function loadAiCompanies() {
  if (!aiCompanySelect) {
    return;
  }

  try {
    const response = await fetch(
      `${API}/fiscal/companies`
    );

    const companies = await response.json();

    if (!response.ok) {
      throw new Error(
        companies.detail ||
        "Erro ao carregar clientes."
      );
    }

    aiCompanySelect.innerHTML =
      companies.map((company) => `
        <option value="${company.id}">
          ${escapeHtml(company.name)}
        </option>
      `).join("");

    const preferred =
      companies.find(
        (company) =>
          Number(company.id) ===
          Number(appContext.companyId)
      ) || companies[0];

    if (!preferred) {
      return;
    }

    aiCompanySelect.value =
      String(preferred.id);

    updateAppContext({
      companyId: preferred.id,
      companyName: preferred.name
    });

    await loadAiCompetences(
      preferred.id,
      true
    );

  } catch (error) {
    aiCompanySelect.innerHTML = `
      <option value="">
        Não foi possível carregar clientes
      </option>
    `;
  }
}


async function loadAiCompetences(
  companyId,
  keepContext = false
) {
  if (!aiCompetenceSelect) {
    return;
  }

  aiCompetenceSelect.disabled = true;

  try {
    const response = await fetch(
      `${API}/fiscal/companies/${companyId}/competences`
    );

    const competences = await response.json();

    if (!response.ok) {
      throw new Error(
        competences.detail ||
        "Erro ao carregar competências."
      );
    }

    const ordered = [
      ...competences
    ].reverse();

    aiCompetenceSelect.innerHTML =
      ordered.map((competence) => `
        <option value="${escapeHtml(competence)}">
          ${formatCompetence(competence)}
        </option>
      `).join("");

    if (ordered.length) {
      const preferred =
        keepContext &&
        ordered.includes(appContext.competence)
          ? appContext.competence
          : ordered[0];

      aiCompetenceSelect.value = preferred;

      updateAppContext({
        competence: preferred
      });
    }

    renderAiContextNote();

  } catch (error) {
    aiCompetenceSelect.innerHTML = `
      <option value="">
        Erro ao carregar competências
      </option>
    `;

  } finally {
    aiCompetenceSelect.disabled = false;
  }
}


function syncAiControlsWithContext() {
  if (
    aiCompanySelect &&
    [...aiCompanySelect.options].some(
      (option) =>
        Number(option.value) ===
        Number(appContext.companyId)
    )
  ) {
    aiCompanySelect.value =
      String(appContext.companyId);
  }

  if (
    aiCompetenceSelect &&
    appContext.competence &&
    [...aiCompetenceSelect.options].some(
      (option) =>
        option.value ===
        appContext.competence
    )
  ) {
    aiCompetenceSelect.value =
      appContext.competence;
  }

  renderAiContextNote();
}


function renderAiContextNote() {
  const note =
    document.getElementById("aiContextNote");

  if (!note) {
    return;
  }

  note.textContent =
    `Contexto ativo: ${appContext.companyName}` +
    `${appContext.competence ? ` · ${formatCompetence(appContext.competence)}` : ""}`;
}


async function askGazarraAI({
  message,
  agent = "auto"
}) {
  if (!message?.trim()) {
    throw new Error(
      "Digite uma pergunta para a GAZARRA IA."
    );
  }

  if (!appContext.companyId) {
    throw new Error(
      "Selecione uma empresa."
    );
  }

  if (!appContext.competence) {
    throw new Error(
      "Selecione uma competência."
    );
  }

  const response = await fetch(
    `${API}/ai/chat`,
    {
      method: "POST",
      headers: {
        "Content-Type":
          "application/json; charset=utf-8"
      },
      body: JSON.stringify({
        company_id:
          Number(appContext.companyId),
        competence:
          appContext.competence,
        message:
          message.trim(),
        agent:
          agent || "auto"
      })
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(
      data.detail ||
      "Não foi possível consultar a GAZARRA IA."
    );
  }

  return data;
}


async function sendAiMessage() {
  if (
    gazarraAiBusy ||
    !aiInput
  ) {
    return;
  }

  const message =
    aiInput.value.trim();

  if (!message) {
    return;
  }

  appendAiMessage(
    "user",
    message
  );

  aiInput.value = "";

  const loadingId =
    appendAiLoading();

  setAiBusy(true);

  try {
    const data = await askGazarraAI({
      message,
      agent:
        aiAgentSelect?.value || "auto"
    });

    removeAiLoading(loadingId);

    appendAiMessage(
      "assistant",
      data.answer,
      data
    );

    renderAiResponseMetadata(data);

  } catch (error) {
    removeAiLoading(loadingId);

    appendAiMessage(
      "error",
      error.message
    );

  } finally {
    setAiBusy(false);
  }
}


async function sendFiscalAiMessage(
  prompt = null
) {
  if (gazarraAiBusy) {
    return;
  }

  const answerBox =
    document.getElementById("fiscalAiAnswer");

  const message =
    (prompt || fiscalAiInput?.value || "")
      .trim();

  if (!message) {
    return;
  }

  if (fiscalAiInput) {
    fiscalAiInput.value = "";
  }

  answerBox.classList.remove("hidden");
  answerBox.innerHTML = `
    <div class="ai-thinking">
      GAZARRA IA analisando o contexto fiscal...
    </div>
  `;

  setAiBusy(true);

  try {
    const data = await askGazarraAI({
      message,
      agent: "auto"
    });

    answerBox.innerHTML = `
      <div class="ai-mini-response">
        <div class="ai-mini-response-head">
          <strong>${escapeHtml(data.agent_title || "GAZARRA IA")}</strong>
          <span>${data.demo_mode ? "Demo" : escapeHtml(data.provider || "IA")}</span>
        </div>
        <div class="ai-answer-text">
          ${formatAiText(data.answer)}
        </div>
        <div class="ai-mini-meta">
          ${data.requires_human_review ? "Requer revisão humana · " : ""}
          ${escapeHtml((data.sources_used || []).join(" · "))}
        </div>
      </div>
    `;

  } catch (error) {
    answerBox.innerHTML = `
      <div class="message error">
        ${escapeHtml(error.message)}
      </div>
    `;

  } finally {
    setAiBusy(false);
  }
}


function appendAiMessage(
  role,
  message,
  metadata = null
) {
  const conversation =
    document.getElementById("aiConversation");

  if (!conversation) {
    return;
  }

  const welcome =
    conversation.querySelector(".ai-welcome");

  if (welcome) {
    welcome.remove();
  }

  const bubble =
    document.createElement("div");

  bubble.className =
    `ai-message ai-message-${role}`;

  if (role === "assistant") {
    bubble.innerHTML = `
      <div class="ai-message-label">
        ${escapeHtml(metadata?.agent_title || "GAZARRA IA")}
      </div>
      <div class="ai-answer-text">
        ${formatAiText(message)}
      </div>
      <div class="ai-message-meta">
        ${metadata?.demo_mode ? "Modo demonstrativo" : escapeHtml(metadata?.provider || "IA")}
        ${metadata?.requires_human_review ? " · revisão humana necessária" : ""}
      </div>
    `;
  }

  else if (role === "user") {
    bubble.innerHTML = `
      <div class="ai-message-label">Você</div>
      <div>${escapeHtml(message)}</div>
    `;
  }

  else {
    bubble.innerHTML = `
      <div class="ai-message-label">Erro</div>
      <div>${escapeHtml(message)}</div>
    `;
  }

  conversation.appendChild(bubble);
  conversation.scrollTop =
    conversation.scrollHeight;
}


function appendAiLoading() {
  const conversation =
    document.getElementById("aiConversation");

  const id =
    `ai-loading-${Date.now()}`;

  if (conversation) {
    conversation.insertAdjacentHTML(
      "beforeend",
      `
        <div id="${id}" class="ai-message ai-message-assistant ai-thinking">
          Analisando contexto e selecionando agente...
        </div>
      `
    );

    conversation.scrollTop =
      conversation.scrollHeight;
  }

  return id;
}


function removeAiLoading(id) {
  document
    .getElementById(id)
    ?.remove();
}


function setAiBusy(value) {
  gazarraAiBusy = value;

  if (btnAiSend) {
    btnAiSend.disabled = value;
    btnAiSend.textContent =
      value ? "Analisando..." : "Enviar";
  }

  if (btnFiscalAiSend) {
    btnFiscalAiSend.disabled = value;
    btnFiscalAiSend.textContent =
      value ? "Analisando..." : "Perguntar à IA";
  }
}


function renderAiResponseMetadata(data) {
  const lastAgent =
    document.getElementById("aiLastAgent");

  const humanReview =
    document.getElementById("aiHumanReview");

  const sources =
    document.getElementById("aiSources");

  if (lastAgent) {
    lastAgent.textContent =
      data.agent_title ||
      data.agent_used ||
      "—";
  }

  if (humanReview) {
    humanReview.textContent =
      data.requires_human_review
        ? "Necessária"
        : "Não indicada";
  }

  if (sources) {
    sources.innerHTML =
      (data.sources_used || [])
        .map((source) => `
          <span>${escapeHtml(source)}</span>
        `)
        .join("") ||
      "<span>Nenhuma fonte informada.</span>";
  }
}


function clearAiConversation() {
  const conversation =
    document.getElementById("aiConversation");

  if (conversation) {
    conversation.innerHTML = `
      <div class="ai-message ai-message-assistant ai-greeting">
        <div class="ai-assistant-avatar">✦</div>
        <div class="ai-message-content">
          <span class="ai-message-label">GAZARRA IA</span>
          <div class="ai-answer-text">
            <p>Olá! Eu sou a <strong>GAZARRA IA</strong>.</p>
            <p>Conversa limpa. Posso ajudar com o fechamento, tributos, XML, mapeamentos e pendências da empresa em contexto.</p>
            <p>Como posso ajudar hoje?</p>
          </div>
        </div>
      </div>
    `;
  }

  const lastAgent =
    document.getElementById("aiLastAgent");

  const humanReview =
    document.getElementById("aiHumanReview");

  const sources =
    document.getElementById("aiSources");

  if (lastAgent) {
    lastAgent.textContent = "—";
  }

  if (humanReview) {
    humanReview.textContent = "—";
  }

  if (sources) {
    sources.innerHTML =
      "<span>Nenhuma consulta realizada.</span>";
  }
}


function formatAiText(value) {
  return escapeHtml(value || "")
    .split("\n\n")
    .map((paragraph) =>
      `<p>${paragraph.replaceAll("\n", "<br>")}</p>`
    )
    .join("");
}


/* =========================================================
   ADMINISTRAÇÃO E SEGREGAÇÃO DE EMPRESAS
========================================================= */

async function initializeAdmin() {
  if (!currentUser || currentUser.role !== "admin") return;
  if (!adminInitialized) adminInitialized = true;
  await Promise.all([loadAdminUsers(), loadAdminAudit()]);
}

async function loadAdminUsers() {
  const output = document.getElementById("adminUsersList");
  if (!output) return;
  try {
    const response = await fetch(`${API}/admin/users`);
    const users = await response.json();
    if (!response.ok) throw new Error(users.detail || "Erro ao carregar usuários.");
    output.innerHTML = users.map((user) => `
      <button class="admin-user-card ${Number(user.id) === Number(adminSelectedUserId) ? "selected" : ""}" type="button" data-user-id="${user.id}" data-user-role="${escapeHtml(user.role)}">
        <span class="admin-user-avatar">${escapeHtml((user.name || "U").charAt(0).toUpperCase())}</span>
        <span><strong>${escapeHtml(user.name)}</strong><small>${escapeHtml(user.email)}</small></span>
        <b class="role-pill ${user.role === "admin" ? "role-admin" : "role-analyst"}">${user.role === "admin" ? "Admin" : "Analista"}</b>
      </button>
    `).join("");

    output.querySelectorAll(".admin-user-card").forEach((button) => {
      button.addEventListener("click", async () => {
        adminSelectedUserId = Number(button.dataset.userId);
        output.querySelectorAll(".admin-user-card").forEach((item) => item.classList.remove("selected"));
        button.classList.add("selected");
        const selectedUser = users.find((user) => Number(user.id) === adminSelectedUserId);
        const text = document.getElementById("adminSelectedUserText");
        const search = document.getElementById("adminCompanySearch");
        const save = document.getElementById("btnSaveAssignments");
        if (text) text.textContent = selectedUser?.role === "admin"
          ? `${selectedUser.name} é administrador e já possui acesso a todas as empresas.`
          : `Defina a carteira de ${selectedUser?.name || "analista"}.`;
        if (search) search.disabled = selectedUser?.role === "admin";
        if (save) save.disabled = selectedUser?.role === "admin";
        await loadAdminCompanies(adminSelectedUserId, "");
      });
    });
  } catch (error) {
    output.innerHTML = `<div class="message error">${escapeHtml(error.message)}</div>`;
  }
}

async function loadAdminCompanies(userId, search = "") {
  const output = document.getElementById("adminCompanyList");
  if (!output || !userId) return;
  try {
    const params = new URLSearchParams();
    if (search.trim()) params.set("search", search.trim());
    const response = await fetch(`${API}/admin/users/${userId}/companies?${params.toString()}`);
    const companies = await response.json();
    if (!response.ok) throw new Error(companies.detail || "Erro ao carregar empresas.");
    output.innerHTML = companies.length ? companies.map((company) => `
      <label class="admin-company-row">
        <input type="checkbox" value="${company.id}" ${company.assigned ? "checked" : ""}/>
        <span><strong>${escapeHtml(company.name)}</strong><small>${escapeHtml(company.cnpj || "CNPJ não informado")}</small></span>
        <b>${company.assigned ? "Atribuída" : "Disponível"}</b>
      </label>
    `).join("") : '<div class="admin-empty">Nenhuma empresa encontrada.</div>';
  } catch (error) {
    output.innerHTML = `<div class="message error">${escapeHtml(error.message)}</div>`;
  }
}

const adminCompanySearch = document.getElementById("adminCompanySearch");
if (adminCompanySearch) {
  let adminSearchTimer = null;
  adminCompanySearch.addEventListener("input", () => {
    clearTimeout(adminSearchTimer);
    adminSearchTimer = setTimeout(() => {
      if (adminSelectedUserId) loadAdminCompanies(adminSelectedUserId, adminCompanySearch.value);
    }, 220);
  });
}

const btnSaveAssignments = document.getElementById("btnSaveAssignments");
if (btnSaveAssignments) {
  btnSaveAssignments.addEventListener("click", async () => {
    if (!adminSelectedUserId) return;
    const ids = [...document.querySelectorAll('#adminCompanyList input[type="checkbox"]:checked')].map((input) => Number(input.value));
    const status = document.getElementById("adminAssignmentStatus");
    try {
      btnSaveAssignments.disabled = true;
      const response = await fetch(`${API}/admin/users/${adminSelectedUserId}/companies`, {
        method: "PUT",
        headers: { "Content-Type": "application/json; charset=utf-8" },
        body: JSON.stringify({ company_ids: ids })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Erro ao salvar empresas.");
      if (status) status.textContent = "Carteira atualizada com sucesso.";
      await Promise.all([loadAdminCompanies(adminSelectedUserId, adminCompanySearch?.value || ""), loadAdminAudit()]);
    } catch (error) {
      if (status) status.textContent = error.message;
    } finally {
      btnSaveAssignments.disabled = false;
    }
  });
}

async function loadAdminAudit() {
  const output = document.getElementById("adminAuditList");
  if (!output) return;
  try {
    const response = await fetch(`${API}/admin/audit?limit=20`);
    const rows = await response.json();
    if (!response.ok) throw new Error(rows.detail || "Erro ao carregar auditoria.");
    output.innerHTML = rows.length ? rows.map((row) => `
      <div class="audit-row"><span class="audit-dot"></span><div><strong>${escapeHtml(row.action)}</strong><small>${escapeHtml(row.entity)} ${escapeHtml(row.entity_id || "")}</small></div><time>${row.created_at ? new Date(row.created_at).toLocaleString("pt-BR") : "—"}</time></div>
    `).join("") : '<div class="admin-empty">Nenhuma alteração registrada ainda.</div>';
  } catch (error) {
    output.innerHTML = `<div class="message error">${escapeHtml(error.message)}</div>`;
  }
}

document.getElementById("btnRefreshAudit")?.addEventListener("click", loadAdminAudit);

const newUserModal = document.getElementById("newUserModal");
function closeNewUserModal() { newUserModal?.classList.add("hidden"); }
document.getElementById("btnNewUser")?.addEventListener("click", () => newUserModal?.classList.remove("hidden"));
document.getElementById("btnCloseNewUser")?.addEventListener("click", closeNewUserModal);
document.getElementById("btnCancelNewUser")?.addEventListener("click", closeNewUserModal);

document.getElementById("btnCreateUser")?.addEventListener("click", async () => {
  const message = document.getElementById("newUserMessage");
  const payload = {
    name: document.getElementById("newUserName").value.trim(),
    email: document.getElementById("newUserEmail").value.trim(),
    password: document.getElementById("newUserPassword").value,
    role: document.getElementById("newUserRole").value
  };
  try {
    const response = await fetch(`${API}/admin/users`, {
      method: "POST",
      headers: { "Content-Type": "application/json; charset=utf-8" },
      body: JSON.stringify(payload)
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Erro ao criar usuário.");
    if (message) { message.textContent = "Usuário criado."; message.classList.remove("hidden"); }
    await loadAdminUsers();
    setTimeout(closeNewUserModal, 650);
  } catch (error) {
    if (message) { message.textContent = error.message; message.classList.remove("hidden"); }
  }
});

/* =========================================================
   AUXILIARES
========================================================= */

function confidenceClass(confidence) {
  if (confidence >= 90) {
    return "confidence-high";
  }

  if (confidence >= 70) {
    return "confidence-medium";
  }

  return "confidence-low";
}


function translateStatus(status) {
  switch (status) {

    case "homologated":
      return {
        label:
          "Homologado",

        className:
          "status-success"
      };


    case "auto_candidate":
      return {
        label:
          "Sugestão automática",

        className:
          "status-info"
      };


    case "review":
      return {
        label:
          "Revisão necessária",

        className:
          "status-warning"
      };


    case "blocked":
      return {
        label:
          "Bloqueado",

        className:
          "status-danger"
      };


    default:
      return {
        label:
          status || "-",

        className:
          ""
      };
  }
}


function escapeHtml(value) {
  if (
    value === null ||
    value === undefined
  ) {
    return "";
  }

  return String(value)
    .replaceAll(
      "&",
      "&amp;"
    )
    .replaceAll(
      "<",
      "&lt;"
    )
    .replaceAll(
      ">",
      "&gt;"
    )
    .replaceAll(
      '"',
      "&quot;"
    )
    .replaceAll(
      "'",
      "&#039;"
    );
}

bootstrapAuth();

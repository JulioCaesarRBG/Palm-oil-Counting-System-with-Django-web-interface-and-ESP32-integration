// SIDEBAR TOGGLE

let sidebarOpen = false;
const sidebar = document.getElementById("sidebar");

function openSidebar() {
  if (!sidebarOpen) {
    sidebar.classList.add("sidebar-responsive");
    sidebarOpen = true;
  }
}

function closeSidebar() {
  if (sidebarOpen) {
    sidebar.classList.remove("sidebar-responsive");
    sidebarOpen = false;
  }
}

// ---------- CHARTS ----------

// PIE CHART
const pieChartOptions = {
  series: [40, 60],
  chart: {
    type: "pie",
    background: "transparent",
    height: 350,
    toolbar: {
      show: false,
    },
  },
  colors: ["#00ab57", "#d50000"],
  labels: ["Ripe", "Raw"],
  dataLabels: {
    enabled: true,
    style: {
      colors: ["#f5f7ff"],
    },
  },
  tooltip: {
    shared: true,
    intersect: false,
    theme: "dark",
  },
  legend: {
    labels: {
      colors: "#f5f7ff",
    },
    show: true,
    position: "bottom",
  },
};

const pieChart = new ApexCharts(
  document.querySelector("#pie-chart"),
  pieChartOptions
);
pieChart.render();

// LINE CHART
const lineChartOptions = {
  series: [
    {
      name: "Ripe",
      data: [31, 40, 28, 51, 42, 109, 100],
    },
    {
      name: "Raw",
      data: [11, 20, 23, 32, 34, 52, 41],
    },
  ],
  chart: {
    type: "line",
    background: "transparent",
    height: 350,
    stacked: false,
    toolbar: {
      show: false,
    },
  },
  colors: ["#00ab57", "#d50000"],
  labels: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul"],
  dataLabels: {
    enabled: false,
  },
  stroke: {
    curve: "smooth",
  },
  xaxis: {
    axisBorder: {
      color: "#55596e",
      show: true,
    },
    axisTicks: {
      color: "#55596e",
      show: true,
    },
    labels: {
      offsetY: 5,
      style: {
        colors: "#f5f7ff",
      },
    },
  },
  yaxis: {
    labels: {
      style: {
        colors: ["#f5f7ff"],
      },
    },
  },
  tooltip: {
    shared: true,
    intersect: false,
    theme: "dark",
  },
  legend: {
    position: "top",
    horizontalAlign: "center",
    labels: {
      colors: "#f5f7ff",
    },
  },
};

const lineChart = new ApexCharts(
  document.querySelector("#area-chart"),
  lineChartOptions
);
lineChart.render();

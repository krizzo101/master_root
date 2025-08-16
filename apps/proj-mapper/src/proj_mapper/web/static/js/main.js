/**
 * Project Mapper Web UI JavaScript
 */

document.addEventListener("DOMContentLoaded", function () {
  // Initialize tooltips
  const tooltipTriggerList = [].slice.call(
    document.querySelectorAll('[data-bs-toggle="tooltip"]')
  );
  tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });

  // Initialize popovers
  const popoverTriggerList = [].slice.call(
    document.querySelectorAll('[data-bs-toggle="popover"]')
  );
  popoverTriggerList.map(function (popoverTriggerEl) {
    return new bootstrap.Popover(popoverTriggerEl);
  });

  // Project analysis form handler
  const analyzeForm = document.getElementById("analyze-form");
  if (analyzeForm) {
    analyzeForm.addEventListener("submit", function (event) {
      event.preventDefault();

      const projectName = analyzeForm.getAttribute("data-project");
      const submitButton = document.getElementById("analyze-button");
      const progressContainer = document.getElementById("progress-container");
      const progressBar = document.getElementById("analysis-progress");

      // Disable button and show progress
      submitButton.disabled = true;
      submitButton.innerHTML =
        '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Analyzing...';
      progressContainer.classList.remove("d-none");

      // Simulate progress (in a real app, this would be updated via AJAX)
      let progress = 0;
      const interval = setInterval(function () {
        progress += 5;
        progressBar.style.width = progress + "%";
        progressBar.setAttribute("aria-valuenow", progress);

        if (progress >= 100) {
          clearInterval(interval);

          // Send AJAX request to analyze project
          fetch(`/analyze/${projectName}`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
          })
            .then((response) => response.json())
            .then((data) => {
              if (data.status === "success") {
                // Show success message
                const alertContainer =
                  document.getElementById("alert-container");
                alertContainer.innerHTML = `
                                <div class="alert alert-success alert-dismissible fade show">
                                    ${data.message}
                                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                                </div>
                            `;

                // Redirect to project details after a delay
                setTimeout(function () {
                  window.location.href = `/project/${projectName}`;
                }, 1500);
              } else {
                // Show error message
                const alertContainer =
                  document.getElementById("alert-container");
                alertContainer.innerHTML = `
                                <div class="alert alert-danger alert-dismissible fade show">
                                    ${data.message}
                                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                                </div>
                            `;

                // Reset button
                submitButton.disabled = false;
                submitButton.innerHTML = "Analyze Project";
              }
            })
            .catch((error) => {
              console.error("Error:", error);

              // Show error message
              const alertContainer = document.getElementById("alert-container");
              alertContainer.innerHTML = `
                            <div class="alert alert-danger alert-dismissible fade show">
                                An error occurred during analysis. Please try again.
                                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                            </div>
                        `;

              // Reset button
              submitButton.disabled = false;
              submitButton.innerHTML = "Analyze Project";
            });
        }
      }, 200);
    });
  }

  // Project tree toggle
  const folderToggles = document.querySelectorAll(".folder-toggle");
  if (folderToggles.length > 0) {
    folderToggles.forEach((toggle) => {
      toggle.addEventListener("click", function () {
        const folderId = this.getAttribute("data-folder");
        const folderContent = document.getElementById(folderId);

        if (folderContent) {
          folderContent.classList.toggle("d-none");

          // Toggle icon
          const icon = this.querySelector("i");
          if (icon) {
            if (icon.classList.contains("fa-folder")) {
              icon.classList.remove("fa-folder");
              icon.classList.add("fa-folder-open");
            } else {
              icon.classList.remove("fa-folder-open");
              icon.classList.add("fa-folder");
            }
          }
        }
      });
    });
  }

  // Initialize relationship visualization if the container exists
  const graphContainer = document.getElementById("relationship-graph");
  if (graphContainer) {
    // This would normally initialize a graph visualization library like D3.js or vis.js
    // For demonstration, we'll just add placeholder text
    graphContainer.innerHTML =
      '<div class="d-flex justify-content-center align-items-center h-100">' +
      '<p class="text-muted">Relationship visualization would be rendered here using D3.js or similar library</p>' +
      "</div>";
  }
});

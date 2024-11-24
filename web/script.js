// Variables for selected file, directory, and tags
let selectedFile = "";
let selectedFile_name = "";
let currdir = null;
let new_toggle_man = false;
let tags = [];
let selectedTagIndex = -1;


// ---------------------------
// Core Functions
// ---------------------------

/**
 * Load files and directories from the current directory.
 */

// Load files or directories
async function loadFiles() {
    try {
        resetFileControls();
        const response = await eel.get_files(currdir)();
        renderFileList(response);
    } catch (error) {
        console.error("Error loading files:", error);
    }
}

// Render the file list
function renderFileList(files) {
    const fileList = document.getElementById("file-list");
    fileList.innerHTML = "";

    files.forEach((item) => {
        const fileItem = document.createElement("div");
        fileItem.className = "file-item";

        // Set the full path as a data attribute
        //fileItem.setAttribute("data-path", item.path);

        const fileIcon = document.createElement("div");
        fileIcon.className = "file-icon";
        fileIcon.innerHTML = item.type === "file" ? getIconHTML(item.name.split('.').pop()) : "📁";

        const fileName = document.createElement("div");
        fileName.className = "file-name";
        fileName.textContent = item.name;

        fileItem.appendChild(fileIcon);
        fileItem.appendChild(fileName);

        fileItem.addEventListener("click", () => {
            if (item.type === "file") {
                displayFileName(item.path, item.name);
            } else {
                currdir = item.path
                loadFiles();
                displayFileName(item.path, item.name);
                updateHeader();
            }
        });

        fileList.appendChild(fileItem);
    });
}

// Reset file controls
function resetFileControls() {
    const fileNameField = document.getElementById("file-name-field");
    const openButton = document.getElementById("open-file-button");
    const moveButton = document.getElementById("move-button");
    const trashButton = document.getElementById("trash-button");

    fileNameField.value = "";
    fileNameField.disabled = true;

    openButton.style.visibility = "hidden";
    openButton.disabled = true;

    moveButton.disabled = true;
    trashButton.disabled = true;

}

// Display selected file or directory name
function displayFileName(filepath, filename) {
    selectedFile = filepath;
    selectedFile_name = filename;

    const fileNameField = document.getElementById("file-name-field");
    const openButton = document.getElementById("open-file-button");
    const moveButton = document.getElementById("move-button");
    const trashButton = document.getElementById("trash-button");

    fileNameField.value = selectedFile_name;
    fileNameField.disabled = false;

    openButton.style.visibility = "visible";
    openButton.disabled = false;

    moveButton.disabled = false;
    trashButton.disabled = false;
}

// Open selected file
async function openSelectedFile() {
    if (!selectedFile) {
        alert("No file selected!");
        return;
    }
    try {
        const response = await eel.open_file(selectedFile)();
        alert(response);
    } catch (error) {
        console.error("Error opening file:", error);
    }
}

// Check if a new path needs to be created
async function checkNewPath() {
    try {
        const tagList = getTags();
        const response = await eel.check_path(tagList)();
        const newToggle = document.getElementById("new-toggle");

        newToggle.checked = response[0] === "DEST_NOT_EXIST" ? true : new_toggle_man;
    } catch (error) {
        console.error("Error checking path:", error);
        alert("An error occurred while checking the path.");
    }
}

// Handle moving the selected file
async function handleMoveFile() {
    if (!selectedFile) {
        alert("No file selected. Please select a file first.");
        return;
    }
    try {
        const tagList = getTags();
        const newToggle = document.getElementById("new-toggle").checked;
        const intelligentToggle = document.getElementById("intelligent-toggle").checked;

        const result = await eel.move_file(selectedFile_name, selectedFile, tagList, newToggle, intelligentToggle)();
        const str = await eel.get_path_status_message(result[0])
        alert(`${str} ${result[1]}`);
        if (result[0] === "SUCCESSFUL") {
            const curr = await eel.go_one_dir_back(selectedFile)()
            currdir = curr 
            updateHeader()
            loadFiles(); // Refresh file list
        }
    } catch (error) {
        console.error("Error moving file:", error);
        alert("An error occurred while moving the file.");
    }
}

// Handle trashing the selected file
async function handleTrashFile() {
    if (!selectedFile) {
        alert("No file selected!");
        return;
    }
    try {
        const response = await eel.move_to_trash(selectedFile)();
        const str = await eel.get_path_status_message(response[0])()
        if (response[0] === "SUCCESSFUL") {
            alert(`${str} trash`);
            const curr = await eel.go_one_dir_back(selectedFile)();
            currdir = curr;
            updateHeader();
            loadFiles(); // Refresh file list
        } else {
            alert(str);
        }
    } catch (error) {
        console.error("Error moving file to trash:", error);
        alert("An error occurred while moving the file to trash.");
    }
}
// Add, render, and manage tags
function addTag() {
    const tagInput = document.getElementById("tag-input");
    const tag = tagInput.value.trim();

    if (tag && !tags.includes(tag)) {
        tags.push(tag);
        renderTags();
        tagInput.value = "";
    }
}

function renderTags() {
    const tagList = document.getElementById("tag-list");
    tagList.innerHTML = "";

    tags.forEach((tag, index) => {
        const tagItem = document.createElement("div");
        tagItem.className = "tag-item";

        // Add selection behavior
        tagItem.addEventListener("click", () => {
            selectedTagIndex = index;
            renderTags(); // Re-render to update selected state
        });

        if (index === selectedTagIndex) {
            tagItem.classList.add("selected");
        }

        const tagName = document.createElement("span");
        tagName.textContent = tag;

        const deleteButton = document.createElement("span");
        deleteButton.textContent = " ×";
        deleteButton.style.cursor = "pointer";
        deleteButton.style.marginLeft = "5px";

        // Handle inline deletion
        deleteButton.addEventListener("click", (event) => {
            event.stopPropagation(); // Prevent selection when deleting
            tags.splice(index, 1);
            selectedTagIndex = -1; // Clear selection
            renderTags();
            checkNewPath(); // Automatically check path after tag update
        });

        tagItem.appendChild(tagName);
        tagItem.appendChild(deleteButton);
        tagList.appendChild(tagItem);
    });

    checkNewPath(); // Automatically check path whenever tags change
}

function removeSelectedTag() {
    if (selectedTagIndex > -1) {
        tags.splice(selectedTagIndex, 1);
        selectedTagIndex = -1;
        renderTags();
        checkNewPath();
    } else {
        alert("No tag selected!");
    }
}

function removeAllTags() {
    tags = [];
    selectedTagIndex = -1;
    renderTags();
    checkNewPath();
}

// Utility functions
function getTags() {
    return tags;
}

function getIconHTML(extension) {
    const icons = {
        pdf: "📄",
        png: "🖼️",
        txt: "📄",
        zip: "🗂️",
        psd: "🖌️",
        avi: "🎥"
    };
    return icons[extension.toLowerCase()] || "📄";
}

// Function to update the header based on `currentDir`
async function updateHeader() {
    const title = document.getElementById("title");
    const invPath = await eel.get_inventory_path()();
    if (currdir === invPath) {
        title.textContent = "My Files";
    } else {
        title.textContent = "Back"; 
    }
}

// Function to handle title click
async function handleTitleClick() {
    const curr = await eel.go_one_dir_back(currdir)()
    currdir = curr 
    loadFiles();      // Reload files for the current state of `dir`
    updateHeader();   // Update header text
}

// ---------------------------
// Event Initialization
// ---------------------------

document.addEventListener("DOMContentLoaded", async () => {
    const title = document.getElementById("title");

    // Set the current directory using inventory path
    currdir = await eel.get_inventory_path()();

    // Add click listener to the title for navigation
    title.addEventListener("click", handleTitleClick);

    // Initialize event listeners and tag suggestions
    initializeEventListeners();
    initializeTagSuggestions();

    // Load initial files and update the header
    loadFiles();
    updateHeader();
});


// Initialize event listeners
function initializeEventListeners() {
    document.getElementById("open-file-button").addEventListener("click", openSelectedFile);
    document.getElementById("move-button").addEventListener("click", handleMoveFile);
    document.getElementById("trash-button").addEventListener("click", handleTrashFile);
    document.getElementById("add-tag-button").addEventListener("click", addTag);
    document.getElementById("remove-selected-tag-button").addEventListener("click", removeSelectedTag);
    document.getElementById("remove-all-tags-button").addEventListener("click", removeAllTags);

    const newToggle = document.getElementById("new-toggle");
    newToggle.addEventListener("change", async() => {
        const tagList = getTags();
        const response = await eel.check_path(tagList)();
        if (response[0] !== "DEST_NOT_EXIST") {
            new_toggle_man = !new_toggle_man;
        }
        checkNewPath()
    });

    const tagInput = document.getElementById("tag-input");
    tagInput.addEventListener("keydown", (event) => {
        if (event.key === "Enter") {
            event.preventDefault();
            addTag();
        }
    });
    const fileNameField = document.getElementById("file-name-field");
    fileNameField.addEventListener("input", (event) => {
        selectedFile_name = event.target.value;
    });
}


// Initialize settings
document.addEventListener("DOMContentLoaded", () => {
    const settingsButton = document.getElementById("settings-button");
    const settingsModal = document.getElementById("settings-modal");
    const closeSettingsButton = document.getElementById("close-settings-button");
    const saveSettingsButton = document.getElementById("save-settings-button");
    const settingsTextarea = document.getElementById("inv-field");
    const rootpathAre = document.getElementById("root-field");


    // Open settings modal
    settingsButton.addEventListener("click", async () => {
        settingsModal.classList.remove("hidden");
        const invresponse = await eel.get_inventory_path()();
        const rootresponse = await eel.get_root_path()();

        settingsTextarea.value = invresponse;
        rootpathAre.value = rootresponse;
    });

    // Close settings modal
    closeSettingsButton.addEventListener("click", () => {
        settingsModal.classList.add("hidden");
    });

   // Save settings and close modal
    saveSettingsButton.addEventListener("click", async () => {
        // Collect paths from textareas
        const inventoryPath = settingsTextarea.value.trim();
        const rootPath = rootpathAre.value.trim();

        try {
            // Call the unified backend function
            const response = await eel.set_paths_with_feedback(inventoryPath, rootPath)();
            
            // Handle the response
            if (response.success) {
                settingsModal.classList.add("hidden"); // Close the modal if successful
                currdir = null;
                loadFiles()
            } else {
                // Show error messages
                alert(`Error setting paths:\n${response.messages.join("\n")}`);
            }
        } catch (error) {
            alert("An unexpected error occurred while saving paths. Please try again.");
            console.error("Error details:", error);
        }
    });
});

// Initialize tag suggestions
function initializeTagSuggestions() {
    const tagInput = document.getElementById("tag-input");
    const suggestionsContainer = document.createElement("div");
    suggestionsContainer.classList.add("tag-suggestions");

    // Append suggestions container to a relatively positioned parent
    const parent = tagInput.parentNode;
    parent.style.position = "relative";
    parent.appendChild(suggestionsContainer);

    tagInput.addEventListener("input", async () => {
        const inputValue = tagInput.value.trim();
        suggestionsContainer.innerHTML = "";

        if (inputValue) {
            try {
                const recommendations = await eel.recommend_tags(inputValue)();
                recommendations.slice(0, 10).forEach((recommendation) => {
                    const suggestion = document.createElement("div");
                    suggestion.className = "tag-suggestion";
                    suggestion.textContent = recommendation;

                    suggestion.addEventListener("click", () => {
                        tagInput.value = recommendation;
                        tagInput.focus();
                        suggestionsContainer.innerHTML = "";
                    });

                    suggestionsContainer.appendChild(suggestion);
                });
            } catch (error) {
                console.error("Error fetching tag suggestions:", error);
            }
        }
    });

    document.addEventListener("click", (event) => {
        if (!parent.contains(event.target)) {
            suggestionsContainer.innerHTML = "";
        }
    });
}



document.addEventListener('DOMContentLoaded', () => {

    const authDiv = document.getElementById('auth');
    const registerDiv = document.getElementById('register');
    const productsDiv = document.getElementById('products');
    const loginMessage = document.getElementById('login-message');
    const registerMessage = document.getElementById('register-message');

    // Handle login type toggle
    const loginTitle = document.getElementById('login-title');
    const loginTypeRadios = document.getElementsByName('login-type');
    loginTypeRadios.forEach(radio => {
        radio.addEventListener('change', () => {
            loginTitle.textContent = radio.value === 'admin' ? 'Admin Login' : 'User Login';
        });
    });

    // Handle login
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', (event) => {
            event.preventDefault(); // Prevent default form submission

            const username = document.getElementById('login-username').value;
            const password = document.getElementById('login-password').value;
            const loginType = [...document.getElementsByName('login-type')].find(radio => radio.checked).value;

            console.log(`Attempting login: Type=${loginType}, Username=${username}`); // Debugging log

            let endpoint;
            if (loginType === 'user') {
                endpoint = '/api/login';
            } else if (loginType === 'sda-admin' || loginType === 'pda-admin') {
                endpoint = '/api/login-admin';
            }

            fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            })
            .then(response => response.json().then(data => ({ status: response.status, body: data })))
            .then(({ status, body }) => {
                if (status !== 200) {
                    console.error(`Login failed: ${body.error}`); // Debugging log
                    alert(`Error: ${body.error}`);
                } else {
                    alert(body.message);
                    if (loginType === 'user') {
                        window.location.href = '/home';
                    } else if (loginType === 'sda-admin') {
                        window.location.href = '/sda';
                    } else if (loginType === 'pda-admin') {
                        window.location.href = '/pda';
                    }
                }
            })
            .catch(error => {
                console.error('Error during login:', error); // Debugging log
                alert('An unexpected error occurred. Please try again.');
            });
        });
    } 

    // Handle registration
    const registerForm = document.getElementById('register-form');
    if (registerForm) {
        registerForm.addEventListener('submit', (event) => {
            event.preventDefault();
            const username = document.getElementById('register-username').value;
            const password = document.getElementById('register-password').value;
            const confirm_password = document.getElementById('register-confirm-password').value;
            const license_code = document.getElementById('register-license-code').value;

            fetch('/api/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password, confirm_password, license_code })
            })
            .then(response => response.json().then(data => ({ status: response.status, body: data })))
            .then(({ status, body }) => {
                if (status !== 201) {
                    alert(`Error: ${body.error}`); // Show error popup
                } else {
                    alert(body.message); // Show success popup
                    window.location.href = '/'; // Redirect to login page
                }
            })
            .catch(error => {
                console.error('Error during registration:', error);
                alert('An unexpected error occurred. Please try again.');
            });
        });
    }

    // Handle "Forget Password" button click
    const forgetPasswordButton = document.getElementById('forget-password');
    if (forgetPasswordButton) {
        forgetPasswordButton.addEventListener('click', () => {
            window.location.href = '/forget'; // Redirect to forget password page
        });
    }

    // Handle "Forget Password" form submission
    const forgetForm = document.getElementById('forget-form');
    if (forgetForm) {
        forgetForm.addEventListener('submit', (event) => {
            event.preventDefault();
            const username = document.getElementById('forget-username').value;

            fetch('/api/forget', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert(data.error); // Show error popup
                } else {
                    document.getElementById('reset-password').style.display = 'block'; // Show reset password section
                    document.getElementById('forget-message').textContent = data.message;
                }
            })
            .catch(error => {
                console.error('Error during forget password:', error);
                alert('An unexpected error occurred. Please try again.');
            });
        });
    }

    // Handle "Reset Password" button click
    const resetPasswordButton = document.getElementById('reset-password-btn');
    if (resetPasswordButton) {
        resetPasswordButton.addEventListener('click', () => {
            const username = document.getElementById('forget-username').value;
            const newPassword = document.getElementById('new-password').value;

            fetch('/api/reset-password', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, newPassword })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert(data.error); // Show error popup
                } else {
                    alert(data.message); // Show success popup
                    window.location.href = '/'; // Redirect to login page
                }
            })
            .catch(error => {
                console.error('Error during reset password:', error);
                alert('An unexpected error occurred. Please try again.');
            });
        });
    }

    // Fetch products
    fetch('/api/products')
        .then(response => response.json())
        .then(products => {
            products.forEach(product => {
                const productElement = document.createElement('div');
                productElement.textContent = `${product.name} - $${product.price}`;
                productsDiv.appendChild(productElement);
            });
        })
        .catch(error => console.error('Error fetching products:', error));

    // Fetch and display registered users and license keys on the SDA page
    if (window.location.pathname === '/sda') {
        // Redirect to Add License Key page
        const addLicenseKeyButton = document.getElementById('add-license-key');
        if (addLicenseKeyButton) {
            addLicenseKeyButton.addEventListener('click', () => {
                window.location.href = '/addlicense';
            });
        }

        // Fetch registered users
        fetch('/api/sda/users')
            .then(response => response.json())
            .then(users => {
                const usersTableBody = document.getElementById('users');
                if (usersTableBody) {
                    usersTableBody.innerHTML = users.map(user => `
                        <tr>
                            <td>${user.username}</td>
                            <td>${user.password}</td>
                            <td>${user.email || 'N/A'}</td>
                            <td>${user.address || 'N/A'}</td>
                            <td><input type="checkbox" class="user-checkbox" data-username="${user.username}"></td>
                            <td><button class="edit-user">Edit</button></td>
                        </tr>
                    `).join('');
                }
            })
            .catch(error => console.error('Error fetching users:', error));

        // Fetch license keys
        fetch('/api/sda/license-keys')
            .then(response => response.json())
            .then(keys => {
                const licenseKeysTableBody = document.getElementById('license-keys');
                if (licenseKeysTableBody) {
                    licenseKeysTableBody.innerHTML = keys.map(key => `
                        <tr>
                            <td>${key.key}</td>
                            <td>${key.active ? 'Active' : 'Inactive'}</td>
                            <td><input type="checkbox" class="key-checkbox" data-key="${key.key}"></td>
                            <td><button class="edit-key">Edit</button></td>
                        </tr>
                    `).join('');
                }
            })
            .catch(error => console.error('Error fetching license keys:', error));

        // Handle deleting selected users
        const deleteUsersButton = document.getElementById('delete-users');
        if (deleteUsersButton) {
            deleteUsersButton.addEventListener('click', () => {
                const selectedUsers = Array.from(document.querySelectorAll('.user-checkbox:checked'))
                    .map(checkbox => checkbox.dataset.username);

                if (selectedUsers.length === 0) {
                    alert('No users selected for deletion.');
                    return;
                }

                fetch('/api/sda/users', {
                    method: 'DELETE',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ usernames: selectedUsers })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        alert(data.error);
                    } else {
                        alert(data.message);
                        window.location.reload();
                    }
                })
                .catch(error => console.error('Error deleting users:', error));
            });
        }

        // Handle deleting selected license keys
        const deleteKeysButton = document.getElementById('delete-keys');
        if (deleteKeysButton) {
            deleteKeysButton.addEventListener('click', () => {
                const selectedKeys = Array.from(document.querySelectorAll('.key-checkbox:checked'))
                    .map(checkbox => checkbox.dataset.key);

                if (selectedKeys.length === 0) {
                    alert('No license keys selected for deletion.');
                    return;
                }

                fetch('/api/sda/license-keys', {
                    method: 'DELETE',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ keys: selectedKeys })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        alert(data.error);
                    } else {
                        alert(data.message);
                        window.location.reload();
                    }
                })
                .catch(error => console.error('Error deleting license keys:', error));
            });
        }

        // Handle adding a new license key
        const addLicenseForm = document.getElementById('add-license-form');
        if (addLicenseForm) {
            addLicenseForm.addEventListener('submit', (event) => {
                event.preventDefault();
                const newLicenseKey = document.getElementById('new-license-key').value;

                fetch('/api/sda/license-keys', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ key: newLicenseKey })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        alert(data.error); // Show error popup
                    } else {
                        alert(data.message); // Show success popup
                        window.location.reload(); // Reload the page to fetch updated data
                    }
                })
                .catch(error => {
                    console.error('Error adding license key:', error);
                    alert('An unexpected error occurred. Please try again.');
                });
            });
        }

        let editMode = null; // Track the current edit mode (users or license keys)
        let editRow = null; // Track the row being edited
        let originalUsername = null; // Track the original username before editing
        let originalLicenseKey = null; // Track the original license key before editing

        // Handle "Edit" button click for users
        document.addEventListener('click', (event) => {
            if (event.target.classList.contains('edit-user')) {
                editMode = 'user';
                editRow = event.target.closest('tr');
                originalUsername = editRow.children[0].textContent.trim(); // Store the original username
                enterEditMode(editRow);
            }
        });

        // Handle "Edit" button click for license keys
        document.addEventListener('click', (event) => {
            if (event.target.classList.contains('edit-key')) {
                editMode = 'key';
                editRow = event.target.closest('tr');
                originalLicenseKey = editRow.children[0].textContent.trim(); // Store the original license key
                enterEditMode(editRow);
            }
        });

        // Enter edit mode
        function enterEditMode(row) {
            const confirmButton = document.getElementById('confirm-edit');
            const cancelButton = document.getElementById('cancel-edit');

            confirmButton.classList.remove('hidden');
            cancelButton.classList.remove('hidden');

            // Make table cells editable
            Array.from(row.children).forEach((cell, index) => {
                if (editMode === 'key' && index === 1) {
                    // Replace "Status" cell with a dropdown
                    const currentStatus = cell.textContent.trim(); // Retain the original status
                    cell.setAttribute('data-original-status', currentStatus); // Store the original status
                    cell.innerHTML = `
                        <select>
                            <option value="Active" ${currentStatus === 'Active' ? 'selected' : ''}>Active</option>
                            <option value="Inactive" ${currentStatus === 'Inactive' ? 'selected' : ''}>Inactive</option>
                        </select>
                    `;
                } else if (index < row.children.length - 2) { // Exclude action buttons
                    cell.contentEditable = true;
                    cell.classList.add('editable-cell');
                }
            });
        }

        // Exit edit mode
        function exitEditMode() {
            const confirmButton = document.getElementById('confirm-edit');
            const cancelButton = document.getElementById('cancel-edit');

            confirmButton.classList.add('hidden');
            cancelButton.classList.add('hidden');

            if (editRow) {
                Array.from(editRow.children).forEach((cell, index) => {
                    if (editMode === 'key' && index === 1) {
                        // Revert dropdown back to plain text with the original status
                        const originalStatus = cell.getAttribute('data-original-status');
                        cell.textContent = originalStatus;
                        cell.removeAttribute('data-original-status');
                    } else {
                        cell.contentEditable = false;
                        cell.classList.remove('editable-cell');
                    }
                });
            }

            editRow = null;
            editMode = null;
        }

        // Handle "Cancel" button click
        const cancelEditButton = document.getElementById('cancel-edit');
        cancelEditButton.addEventListener('click', exitEditMode);

        // Handle "Confirm" button click
        const confirmEditButton = document.getElementById('confirm-edit');
        confirmEditButton.addEventListener('click', () => {
            if (!editRow || !editMode) return;

            const confirmButton = document.getElementById('confirm-edit');
            confirmButton.classList.add('hidden');

            // Collect updated data
            const updatedData = Array.from(editRow.children).map((cell, index) => {
                if (editMode === 'key' && index === 1) {
                    // Get the selected value from the dropdown
                    return cell.querySelector('select').value;
                }
                return cell.textContent.trim();
            });

            const endpoint = editMode === 'user' ? '/api/sda/users' : '/api/sda/license-keys';
            const payload = editMode === 'user'
                ? { originalUsername, username: updatedData[0], password: updatedData[1], email: updatedData[2], address: updatedData[3] }
                : { originalKey: originalLicenseKey, key: updatedData[0], active: updatedData[1] === 'Active' };

            // Send updated data to the server
            fetch(endpoint, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            })
                .then((response) => response.json())
                .then((data) => {
                    if (data.error) {
                        alert(`Error: ${data.error}`);
                    } else {
                        alert('Data updated successfully!');
                        window.location.reload();
                    }
                })
                .catch((error) => console.error('Error updating data:', error));
        });
    }

    if (window.location.pathname === '/addlicense') {
        const addLicenseForm = document.getElementById('add-license-form');
        if (addLicenseForm) {
            addLicenseForm.addEventListener('submit', (event) => {
                event.preventDefault();
                const newLicenseKey = document.getElementById('new-license-key').value;

                fetch('/api/sda/license-keys', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ key: newLicenseKey })
                })
                .then(response => response.json())
                .then(data => {
                    const messageElement = document.getElementById('add-license-message');
                    if (data.error) {
                        messageElement.textContent = `Error: ${data.error}`;
                        messageElement.style.color = 'red';
                    } else {
                        messageElement.textContent = 'License key added successfully!';
                        messageElement.style.color = 'green';
                        addLicenseForm.reset(); // Clear the form
                    }
                })
                .catch(error => {
                    console.error('Error adding license key:', error);
                    alert('An unexpected error occurred. Please try again.');
                });
            });
        }
    }

    // Handle Logout button click
    const logoutButton = document.getElementById('logout-button');
    if (logoutButton) {
        logoutButton.addEventListener('click', () => {
            const confirmLogout = confirm('Are you sure you want to log out?');
            if (confirmLogout) {
                fetch('/api/logout', { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        alert(data.message);
                        window.location.href = '/'; // Redirect to login page
                    })
                    .catch(error => console.error('Error during logout:', error));
            }
        });
    }

    if (window.location.pathname === '/user-info') {
        const userInfoForm = document.getElementById('user-info-form');
        const updateMessage = document.getElementById('update-message');
    
        // Fetch user information
        fetch('/api/user-info')
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert(data.error); // Show error popup
                } else {
                    // Pre-fill the form fields with the original data
                    document.getElementById('username').value = data.username;
                    document.getElementById('password').value = data.password;
                    document.getElementById('email').value = data.email || '';
                    document.getElementById('address').value = data.address || '';
                }
            })
            .catch(error => console.error('Error fetching user info:', error));
    
        // Handle form submission
        userInfoForm.addEventListener('submit', (event) => {
            event.preventDefault();
    
            const username = document.getElementById('username').value.trim();
            const password = document.getElementById('password').value.trim();
            const email = document.getElementById('email').value.trim();
            const address = document.getElementById('address').value.trim();
    
            if (!username || !password) {
                alert('Username and password cannot be blank.'); // Show error popup
                return;
            }
    
            if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
                alert('Invalid email format.'); // Show error popup
                return;
            }
    
            fetch('/api/user-info', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password, email, address })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert(data.error); // Show error popup
                } else {
                    alert('Information updated successfully!'); // Show success popup
                    updateMessage.textContent = '';
                }
            })
            .catch(error => {
                console.error('Error updating user info:', error);
                alert('An unexpected error occurred.'); // Show error popup
            });
        });
    }

    if (window.location.pathname === '/home') {
        const welcomeMessage = "Welcome evil users, purchase any items you want, as long as they help you dominate the world. Wish you world go BOOM!";
        const welcomeElement = document.getElementById('welcome-message');
        let index = 0;

        function typeMessage() {
            if (index < welcomeMessage.length) {
                welcomeElement.textContent += welcomeMessage[index];
                index++;
                setTimeout(typeMessage, 50); // Adjust typing speed here
            }
        }

        if (welcomeElement) {
            typeMessage();
        }
    }

    if (window.location.pathname === '/pda') {
        fetch('/api/products')
            .then(response => response.json())
            .then(products => {
                const productList = document.getElementById('product-list');
                productList.innerHTML = products.map(product => `
                    <div class="product">
                        <img src="${product.image}" alt="${product.name}" />
                        <h3>${product.name}</h3>
                        <p>Category: ${product.category}</p>
                        <p>Price: $${product.price.toFixed(2)}</p>
                        <p>Quantity: ${product.quantity}</p>
                        <p>${product.description}</p>
                    </div>
                `).join('');
            })
            .catch(error => console.error('Error fetching products:', error));
    }
});

document.addEventListener('DOMContentLoaded', function () {
    // Organic Cultivation Guidance Form
    const organicForm = document.getElementById('organic-guidance-form');
    if (organicForm) {
        organicForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const buttonText = document.getElementById('button-text');
            const loadingSpinner = document.getElementById('loading-spinner');
            const cropName = document.getElementById('crop-name').value;

            // Show loading spinner and disable button
            buttonText.style.display = 'none';
            loadingSpinner.style.display = 'inline-block';
            organicForm.querySelector('button').disabled = true;

            fetch('/get-organic-guidance', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ crop: cropName }),
            })
            .then(response => response.json())
            .then(data => {
                document.getElementById('organic-guide-text').innerText = data.guide;
                document.getElementById('organic-results').style.display = 'block';
            })
            .catch(error => {
                console.error('Error:', error);
                document.getElementById('organic-guide-text').innerText = 'Failed to fetch guide. Please try again.';
                document.getElementById('organic-results').style.display = 'block';
            })
            .finally(() => {
                // Hide loading spinner and enable button
                buttonText.style.display = 'inline-block';
                loadingSpinner.style.display = 'none';
                organicForm.querySelector('button').disabled = false;
            });
        });
    }

    // Crop Yield Optimization Form
    const yieldForm = document.getElementById('yield-optimization-form');
    if (yieldForm) {
        yieldForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const buttonText = document.getElementById('button-text');
            const loadingSpinner = document.getElementById('loading-spinner');
            const cropName = document.getElementById('crop-name').value;

            // Show loading spinner and disable button
            buttonText.style.display = 'none';
            loadingSpinner.style.display = 'inline-block';
            yieldForm.querySelector('button').disabled = true;

            fetch('/get-yield-optimization', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ crop: cropName }),
            })
            .then(response => response.json())
            .then(data => {
                document.getElementById('yield-guide-text').innerText = data.guide;
                document.getElementById('yield-results').style.display = 'block';
            })
            .catch(error => {
                console.error('Error:', error);
                document.getElementById('yield-guide-text').innerText = 'Failed to fetch guide. Please try again.';
                document.getElementById('yield-results').style.display = 'block';
            })
            .finally(() => {
                // Hide loading spinner and enable button
                buttonText.style.display = 'inline-block';
                loadingSpinner.style.display = 'none';
                yieldForm.querySelector('button').disabled = false;
            });
        });
    }

    // Get Solution Button for Disease Detection
    const getSolutionBtn = document.getElementById('get-solution-btn');
    if (getSolutionBtn) {
        getSolutionBtn.addEventListener('click', function () {
            const buttonText = document.getElementById('button-text');
            const loadingSpinner = document.getElementById('loading-spinner');
            const aiResponse = document.getElementById('ai-response');
            const solutionText = document.getElementById('solution-text');

            // Show loading spinner and disable button
            buttonText.style.display = 'none';
            loadingSpinner.style.display = 'inline-block';
            getSolutionBtn.disabled = true;

            // Get the detected disease from the results list
            const diseaseName = document.querySelector('#results-list li')?.innerText.split(' (')[0];

            if (!diseaseName) {
                alert('No disease detected. Please upload an image first.');
                buttonText.style.display = 'inline-block';
                loadingSpinner.style.display = 'none';
                getSolutionBtn.disabled = false;
                return;
            }

            // Fetch the solution from the backend
            fetch('/get-disease-solution', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ disease: diseaseName }),
            })
            .then(response => response.json())
            .then(data => {
                // Display the solution
                solutionText.innerHTML = data.solution;
                aiResponse.style.display = 'block';
            })
            .catch(error => {
                console.error('Error:', error);
                solutionText.innerHTML = 'Failed to fetch solution. Please try again.';
                aiResponse.style.display = 'block';
            })
            .finally(() => {
                // Hide loading spinner and enable button
                buttonText.style.display = 'inline-block';
                loadingSpinner.style.display = 'none';
                getSolutionBtn.disabled = false;
            });
        });
    }
});
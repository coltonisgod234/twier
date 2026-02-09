// useful functions to load scripts

function loadScript(url, callback) {
    const script = document.createElement('script');
    script.src = url;
    script.async = false;
    script.defer = true;
    script.onload = callback; // optional
    document.head.appendChild(script);
}

function loadScriptAsync(url) {
    return new Promise((resolve, reject) => {
        const script = document.createElement('script');
        script.src = url;
        script.async = false;
        script.onload = resolve;
        script.onerror = reject;
        document.head.appendChild(script);
    });
}

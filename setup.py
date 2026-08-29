from setuptools import setup, find_packages

setup(
    name="auto-content-scraper-win",
    version="1.0.0",
    description="自动抓取网上优质内容/资源站/下载站 - Windows 版",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="qiuqiu-dot",
    url="https://github.com/qiuqiu-dot/auto-content-scraper-win",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.0",
        "lxml>=4.9.0",
    ],
    extras_require={
        "dev": ["pytest", "black", "flake8"],
    },
    entry_points={
        "console_scripts": [
            "auto-content-scraper=scraper.main:main",
        ],
    },
    python_requires=">=3.10",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Utilities",
    ],
)

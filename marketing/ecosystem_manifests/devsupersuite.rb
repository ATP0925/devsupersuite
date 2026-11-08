class Devsupersuite < Formula
  desc "Local-first AST context slicer & pre-commit entropy defense"
  homepage "https://devsupersuite.web.app"
  version "1.0.0"
  license "Proprietary"

  on_macos do
    if Hardware::CPU.arm?
      url "https://devsupersuite.web.app/releases/v1.0.0/devsupersuite-darwin-arm64.tar.gz"
      sha256 "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    else
      url "https://devsupersuite.web.app/releases/v1.0.0/devsupersuite-darwin-x86_64.tar.gz"
      sha256 "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    end
  end

  on_linux do
    url "https://devsupersuite.web.app/releases/v1.0.0/devsupersuite-linux-x86_64.tar.gz"
    sha256 "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
  end

  def install
    bin.install "devsupersuite"
  end

  test do
    assert_match "DevSuperSuite v1.0.0", shell_output("#{bin}/devsupersuite --version")
    assert_match "AST parser initialized", shell_output("#{bin}/devsupersuite check --dry-run")
  end
end

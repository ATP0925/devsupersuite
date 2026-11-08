-- DevSuperSuite Neovim Plugin Specification
-- Author: DevSuperSuite Ecosystem Engineering <ecosystem@devsupersuite.com>
-- License: Proprietary | https://devsupersuite.web.app

return {
  "devsupersuite/devsupersuite.nvim",
  event = { "BufReadPost", "BufNewFile" },
  opts = {
    entropy_threshold = 4.5,
    enforce_test_invariants = true,
    zero_telemetry = true,
  },
  config = function(_, opts)
    local dss = require("devsupersuite")
    dss.setup(opts)

    -- Keybindings for sub-millisecond AST interface extraction
    vim.keymap.set("n", "<leader>ds", function()
      dss.slice_current_buffer()
    end, { desc = "DevSuperSuite: Slice Buffer to AST Interface" })

    vim.keymap.set("n", "<leader>de", function()
      dss.scan_staged_entropy()
    end, { desc = "DevSuperSuite: Scan Staged Entropy (H > 4.5)" })

    vim.keymap.set("n", "<leader>di", function()
      dss.verify_test_invariants()
    end, { desc = "DevSuperSuite: Verify Test Invariants" })
  end,
}

// Vietnamese is the source dictionary: every other language must provide the same keys (en.ts is
// typed against this one). Financial terms follow Vietnamese Accounting Standards wording; the
// glossary is documented in docs/GLOSSARY.md and needs a native-speaker review (P2-4.12).

const unit = (currency: string) => (currency === "VND" ? "đồng" : currency);

export const vi = {
  meta: {
    description: "Khám phá đầu tư Việt Nam.",
    titles: {
      companies: "Doanh nghiệp",
      company: "Doanh nghiệp",
      sectors: "Ngành",
      sector: "Ngành",
      watchlist: "Danh sách theo dõi",
      notFound: "Không tìm thấy",
    },
  },
  shell: {
    tagline: "Khám phá đầu tư Việt Nam",
    navLabel: "Điều hướng chính",
    nav: {
      discover: "Khám phá",
      sectors: "Ngành",
      companies: "Doanh nghiệp",
      watchlist: "Danh sách theo dõi",
    },
    menu: "Menu",
    close: "Đóng",
    language: "Chọn ngôn ngữ",
  },
  status: {
    ok: "API và cơ sở dữ liệu đang hoạt động",
    degraded: "API hoạt động, không kết nối được cơ sở dữ liệu",
    error: "API trả về lỗi",
    offline: "Không kết nối được API",
    pending: "Đang kiểm tra dịch vụ…",
  },
  errors: {
    unreachable: "API của ATLAS không phản hồi. Hãy kiểm tra backend đang chạy rồi tải lại trang.",
    badResponse: "API của ATLAS trả về dữ liệu không đọc được.",
    notFound: "Không tìm thấy.",
    invalidQuery: "Giá trị tìm kiếm hoặc bộ lọc không hợp lệ.",
    server: (status: number | null) => `API của ATLAS trả về lỗi (${status ?? "?"}).`,
  },
  common: {
    loading: "Đang tải…",
    none: "—",
    sampleBadge: "Dữ liệu mẫu",
    sampleTitle: "Bản ghi hư cấu từ bộ dữ liệu mẫu của ATLAS. Không phải doanh nghiệp có thật.",
  },
  discover: {
    title: "Khám phá thị trường niêm yết Việt Nam",
    intro:
      "Tìm hiểu các ngành, doanh nghiệp và nơi họ hoạt động. Không gian làm việc sẽ được bổ sung khi nguồn dữ liệu thị trường được kết nối.",
    emptyTitle: "Chưa kết nối dữ liệu thị trường",
    emptyBody:
      "ATLAS chỉ hiển thị số liệu có nguồn được kiểm chứng, nên hiện chưa có gì ở đây. Khi một nguồn dữ liệu được kết nối, các ngành và doanh nghiệp sẽ xuất hiện tại đây.",
    worldTitle: "Bản đồ hoạt động",
    worldBody:
      "Bản đồ tương tác về nơi các doanh nghiệp Việt Nam hoạt động sẽ có trong một phiên bản sau.",
  },
  companies: {
    title: "Doanh nghiệp",
    intro: "Tra cứu các doanh nghiệp niêm yết trên HOSE, HNX và UPCoM và tìm hiểu hoạt động của họ.",
    query: "Mã cổ phiếu hoặc tên",
    sector: "Ngành",
    allSectors: "Tất cả ngành",
    exchange: "Sàn",
    allExchanges: "Tất cả sàn",
    search: "Tìm kiếm",
    clear: "Xóa bộ lọc",
    count: (n: number) => `${n} doanh nghiệp`,
    loadError: "Không tải được danh sách doanh nghiệp",
    noMatchTitle: "Không có doanh nghiệp phù hợp",
    noMatchBody: "Hãy thử mã cổ phiếu hoặc tên khác, hoặc bỏ bộ lọc ngành và sàn.",
    noneTitle: "Chưa có doanh nghiệp",
    noneBody:
      "Hồ sơ doanh nghiệp sẽ xuất hiện khi được nhập kèm bằng chứng nguồn. Xem hướng dẫn nhập dữ liệu trong docs/DEVELOPMENT.md.",
  },
  pagination: {
    label: "Phân trang",
    previous: "Trang trước",
    next: "Trang sau",
    pageOf: (page: number, pages: number) => `Trang ${page}/${pages}`,
  },
  company: {
    back: "Doanh nghiệp",
    loadError: "Không tải được thông tin doanh nghiệp",
    sampleNotice:
      "Đây là bản ghi hư cấu trong bộ dữ liệu mẫu của ATLAS. Nó không mô tả một doanh nghiệp có thật.",
    sector: "Ngành",
    taxCode: "Mã số thuế",
    website: "Trang web",
    lastVerified: "Lần xác minh gần nhất",
    notVerified: "Chưa được xác minh",
    about: "Giới thiệu",
    listings: "Niêm yết",
    ticker: "Mã CK",
    exchange: "Sàn",
    type: "Loại chứng khoán",
    status: "Trạng thái",
    listed: "Ngày niêm yết",
    statements: "Báo cáo tài chính",
    noStatements: "Chưa có báo cáo tài chính nào được nhập cho doanh nghiệp này.",
    period: (year: number, quarter: number | null) =>
      quarter ? `Quý ${quarter}/${year}` : `Năm tài chính ${year}`,
    restated: (revision: number) => `đã điều chỉnh (lần ${revision})`,
    range: (from: string, to: string) => `Từ ${from} đến ${to}`,
    source: "nguồn",
    sources: "Nguồn tài liệu",
    noSources: "Chưa có bằng chứng nguồn nào được ghi nhận cho doanh nghiệp này.",
    retrieved: (date: string) => `truy xuất ${date}`,
    usageRights: "quyền sử dụng",
    figure: {
      source: "Nguồn",
      page: (page: number) => `Trang ${page}`,
      noPage: "Chưa có số trang nguồn",
      noLink: "Liên kết nguồn không khả dụng",
      untitled: "Tài liệu không có tiêu đề",
      open: (metric: string, title: string, page: number | null) =>
        `Mở tài liệu gốc cho chỉ tiêu ${metric}: ${title}${page === null ? " (chưa có số trang)" : `, trang ${page}`} (mở trong thẻ mới)`,
      reported: (value: string, scale: string) => `Giá trị báo cáo: ${value} ${scale}`,
      scale: (factor: number, currency: string) =>
        `${factor === 1000 ? "nghìn" : factor === 1000000 ? "triệu" : `× ${factor}`} ${unit(currency)}`,
    },
    calculated: {
      title: "Chỉ số tính toán (do ATLAS tính)",
      note: "ATLAS tính các chỉ số này khi bạn xem, từ số liệu báo cáo năm ở trên. Đây không phải số liệu doanh nghiệp công bố và không được lưu lại.",
      none: "Chưa có báo cáo kết quả kinh doanh năm nào để tính chỉ số.",
      verification: {
        all_verified: "Tính từ số liệu đã kiểm chứng",
        some_unverified: "Tính từ số liệu chưa kiểm chứng",
        sample: "Dữ liệu mẫu",
      },
      howTo: "Cách tính",
      role: { numerator: "Tử số", denominator_closing: "Cuối kỳ", denominator_opening: "Đầu kỳ" },
      average: (value: string) => `Bình quân mẫu số: ${value}`,
      reason: {
        missing_input: (metric: string) => `Không tính được: thiếu số liệu đầu vào (${metric})`,
        missing_opening_balance: "Không tính được: thiếu số dư đầu kỳ",
        ambiguous_opening_balance: "Không tính được: có nhiều hơn một số dư đầu kỳ phù hợp",
        input_disputed_or_rejected: "Không tính được: số liệu đầu vào đang xem xét lại hoặc bị loại",
        input_superseded: "Không tính được: tài liệu nguồn đã được thay thế",
        unit_mismatch: "Không tính được: đơn vị không khớp",
        equity_not_positive: "Không có ý nghĩa: vốn chủ sở hữu không dương",
        assets_not_positive: "Không có ý nghĩa: tổng tài sản không dương",
      },
    },
  },
  sectors: {
    title: "Ngành",
    intro: "So sánh các ngành trên các sàn chứng khoán Việt Nam, từ ngân hàng đến logistics.",
    loadError: "Không tải được danh sách ngành",
    noneTitle: "Chưa có ngành",
    noneBody: "Danh mục ngành được nạp khi backend khởi động. Hãy khởi động lại backend để nạp dữ liệu.",
    count: (n: number) => `${n} doanh nghiệp`,
    taxonomyNote: (version: string) =>
      `Phân ngành ATLAS v${version}: cách nhóm riêng của ATLAS theo lĩnh vực kinh doanh chính, không phải phân ngành chính thức của HOSE, HNX hay Ủy ban Chứng khoán Nhà nước.`,
  },
  sector: {
    back: "Ngành",
    loadError: "Không tải được thông tin ngành",
    companiesLoadError: "Không tải được các doanh nghiệp trong ngành",
    noneTitle: "Chưa có doanh nghiệp trong ngành này",
    noneBody: "Doanh nghiệp sẽ xuất hiện ở đây khi được nhập kèm bằng chứng cho ngành này.",
  },
  watchlist: {
    title: "Danh sách theo dõi",
    intro: "Lưu các doanh nghiệp bạn đang tìm hiểu ở một nơi.",
    emptyTitle: "Danh sách theo dõi đang trống",
    emptyBody: "Tính năng lưu doanh nghiệp sẽ có khi hồ sơ doanh nghiệp được công bố.",
  },
  notFound: {
    title: "Không tìm thấy trang",
    body: "Trang hoặc bản ghi bạn tìm không tồn tại.",
    home: "Về trang Khám phá",
  },
  glossary: {
    statementType: {
      income_statement: "Báo cáo kết quả kinh doanh",
      balance_sheet: "Bảng cân đối kế toán",
      cash_flow: "Báo cáo lưu chuyển tiền tệ",
    },
    scope: { consolidated: "Hợp nhất", separate: "Riêng" },
    listingStatus: {
      pending: "Chờ niêm yết",
      listed: "Đang niêm yết",
      suspended: "Tạm ngừng giao dịch",
      delisted: "Đã hủy niêm yết",
    },
    securityType: {
      common_stock: "Cổ phiếu phổ thông",
      preferred_stock: "Cổ phiếu ưu đãi",
      fund_certificate: "Chứng chỉ quỹ",
      bond: "Trái phiếu",
      covered_warrant: "Chứng quyền có bảo đảm",
      other: "Khác",
    },
    verification: {
      unverified: "Chưa xác minh",
      verified: "Đã xác minh",
      disputed: "Đang xem xét lại",
      rejected: "Bị loại",
      superseded: "Đã được thay thế",
      sample: "Dữ liệu mẫu",
    },
    usage: {
      unknown: "Chưa rõ",
      personal_only: "Chỉ dùng cá nhân",
      licensed: "Có giấy phép",
      public_official: "Công bố chính thức",
      restricted: "Hạn chế",
    },
    unit: {
      currency: unit,
      perShare: (currency: string) => `${unit(currency)}/cổ phiếu`,
      shares: "cổ phiếu",
    },
  },
};

export type Dictionary = typeof vi;
